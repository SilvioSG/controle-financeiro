"""
tabs/transacoes.py — Aba de Transações (criar, listar, buscar, editar, importar CSV).
"""
import streamlit as st
import pandas as pd
import html
from datetime import date, datetime

from core.utils import fmt, fmt_data_pt, MESES_PT
from core.models import get_contas, get_categorias, get_transacoes_mes
from components.cards import sec
from intelligence.categorizer import sugerir_categoria, aprender_categoria


def _processar_recorrentes(conn, prefixo_mes):
    """Processa transações recorrentes para o mês atual (Fase 2.1)."""
    # Encontrar mês anterior
    ano, mes = int(prefixo_mes[:4]), int(prefixo_mes[5:7])
    mes_ant = mes - 1
    ano_ant = ano
    if mes_ant <= 0:
        mes_ant = 12
        ano_ant -= 1
    prefixo_ant = f"{ano_ant}-{mes_ant:02d}"

    # Buscar recorrentes do mês anterior que não foram clonadas para este mês
    recorrentes = conn.execute("""
        SELECT t.id, t.tipo, t.descricao, t.valor, t.categoria_id, t.conta_id, t.observacao
        FROM transacoes t
        WHERE t.recorrente = 1 AND t.data LIKE ?
        AND t.id NOT IN (
            SELECT transacao_origem_id FROM recorrentes_log WHERE prefixo_mes = ?
        )
    """, (f"{prefixo_ant}%", prefixo_mes)).fetchall()

    if recorrentes:
        data_lancamento = f"{prefixo_mes}-01"
        count = 0
        for r in recorrentes:
            conn.execute(
                "INSERT INTO transacoes (tipo,descricao,valor,data,categoria_id,conta_id,recorrente,observacao) "
                "VALUES (?,?,?,?,?,?,1,?)",
                (r[1], r[2], r[3], data_lancamento, r[4], r[5], r[6] or ""),
            )
            conn.execute(
                "INSERT OR IGNORE INTO recorrentes_log (prefixo_mes, transacao_origem_id, processado_em) "
                "VALUES (?,?,?)",
                (prefixo_mes, r[0], datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            )
            count += 1
        conn.commit()
        return count
    return 0


def render(ctx):
    """Renderiza a aba Transações."""
    conn = ctx["conn"]
    prefixo_mes = ctx["prefixo_mes"]
    mes_sel = ctx["mes_sel"]

    # ── Processar recorrentes automaticamente ─────────────────────────
    count_rec = _processar_recorrentes(conn, prefixo_mes)
    if count_rec > 0:
        st.success(f"🔄 {count_rec} transação(ões) recorrente(s) lançada(s) automaticamente!")

    # ── Nova Transação ────────────────────────────────────────────────
    sec("➕", "Nova Transação")
    contas_df = get_contas(conn)
    categorias_df = get_categorias(conn)

    with st.form("form_tx", clear_on_submit=True):
        f1, f2 = st.columns(2)
        with f1:
            tipo_tx = st.selectbox(
                "Tipo", ["despesa", "receita"],
                format_func=lambda x: "🔴 Despesa" if x == "despesa" else "🟢 Receita",
            )
        with f2:
            data_tx = st.date_input("Data", value=date.today())
        f3, f4 = st.columns(2)
        with f3:
            desc_tx = st.text_input("Descrição", placeholder="Ex: Supermercado, Salário...")
        with f4:
            valor_tx = st.number_input("Valor (R$)", min_value=0.01, step=10.0, format="%.2f")
        f5, f6 = st.columns(2)
        with f5:
            if not categorias_df.empty:
                co = {f"{r['icone']} {r['nome']} ({r['tipo']})": r["id"] for _, r in categorias_df.iterrows()}
                cs = st.selectbox("Categoria", list(co.keys()))
                cat_id = co[cs]
            else:
                st.warning("Sem categorias.")
                cat_id = None
        with f6:
            if not contas_df.empty:
                co2 = {f"{r['icone']} {r['nome']}": r["id"] for _, r in contas_df.iterrows()}
                cs2 = st.selectbox("Conta", list(co2.keys()))
                conta_id = co2[cs2]
            else:
                st.warning("Sem contas.")
                conta_id = None

        f7, f8 = st.columns(2)
        with f7:
            obs_tx = st.text_input("Observação (opcional)", placeholder="Ex: Dividido com João...")
        with f8:
            tags_tx = st.text_input("Tags (separadas por vírgula)", placeholder="Ex: viagem, lazer")
            
        f9, f10 = st.columns(2)
        with f9:
            recorrente_tx = st.checkbox("🔄 Lançamento Recorrente (Conta Fixa Mensal)")
        with f10:
            parcelado_tx = st.checkbox("💳 Compra Parcelada")
            if parcelado_tx:
                qtd_parcelas = st.number_input("Número de Parcelas", min_value=2, max_value=72, value=2, step=1)
            else:
                qtd_parcelas = 1

        if st.form_submit_button("💾 Salvar Transação", width='stretch', type="primary"):
            if desc_tx.strip() and valor_tx > 0 and cat_id and conta_id:
                # Tratar parcelamento (Fase 2.1)
                from dateutil.relativedelta import relativedelta
                
                try:
                    for i in range(qtd_parcelas):
                        desc_atual = f"{desc_tx.strip()} ({i+1}/{qtd_parcelas})" if qtd_parcelas > 1 else desc_tx.strip()
                        valor_atual = valor_tx / qtd_parcelas if qtd_parcelas > 1 else valor_tx
                        data_atual = (data_tx + relativedelta(months=i)).strftime("%Y-%m-%d")
                        rec_val = 1 if (recorrente_tx and qtd_parcelas == 1) else 0 # Não pode ser parcelado E recorrente infinito ao mesmo tempo
                        
                        cursor = conn.execute(
                            "INSERT INTO transacoes (tipo,descricao,valor,data,categoria_id,conta_id,recorrente,observacao) "
                            "VALUES (?,?,?,?,?,?,?,?)",
                            (tipo_tx, desc_atual, valor_atual, data_atual,
                             cat_id, conta_id, rec_val, obs_tx.strip()),
                        )
                        tx_id = cursor.lastrowid
                        
                        if tags_tx.strip():
                            from core.utils import processar_tags
                            processar_tags(conn, tx_id, tags_tx)
                            
                    aprender_categoria(conn, desc_tx, cat_id)
                    conn.commit()
                    from core.models import clear_cache_transacoes
                    clear_cache_transacoes()
                    st.toast(f"✅ Transação salva!" if qtd_parcelas == 1 else f"✅ Compra parcelada salva em {qtd_parcelas}x!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

            else:
                st.error("Preencha todos os campos.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Importar CSV ──────────────────────────────────────────────────
    with st.expander("📥 Importar Extrato (CSV)"):
        st.info("O CSV deve ter as colunas: **Data** (YYYY-MM-DD), **Descrição**, **Valor** e **Tipo** (receita/despesa).")
        uploaded_file = st.file_uploader("Escolha um arquivo CSV", type=["csv"])
        if uploaded_file is not None and not contas_df.empty:
            try:
                df_csv = pd.read_csv(uploaded_file)
                st.write("Pré-visualização:")
                st.dataframe(df_csv.head(3))
                co2_keys = list(co2.keys()) if not contas_df.empty else []
                c_imp = st.selectbox("Importar para a conta:", co2_keys, key="conta_csv")

                if st.button("Confirmar Importação", type="primary"):
                    conta_id_imp = co2[c_imp]
                    inseridos = 0
                    for _, row in df_csv.iterrows():
                        dt = str(row.get("Data", date.today().strftime("%Y-%m-%d")))
                        desc = str(row.get("Descrição", "Importado"))
                        val = abs(float(row.get("Valor", 0)))
                        tp = str(row.get("Tipo", "despesa")).lower()
                        if tp not in ["receita", "despesa"]:
                            tp = "despesa"
                        
                        sug_cat_id, _ = sugerir_categoria(conn, desc)
                        cat_id_imp = sug_cat_id if sug_cat_id else (categorias_df["id"].iloc[0] if not categorias_df.empty else None)
                        
                        if val > 0 and cat_id_imp:
                            conn.execute(
                                "INSERT INTO transacoes (tipo,descricao,valor,data,categoria_id,conta_id,recorrente) "
                                "VALUES (?,?,?,?,?,?,0)",
                                (tp, desc, val, dt, cat_id_imp, conta_id_imp),
                            )
                            inseridos += 1
                    conn.commit()
                    from core.models import clear_cache_transacoes
                    clear_cache_transacoes()
                    st.toast(f"✅ {inseridos} transações importadas com sucesso!")
                    st.rerun()
            except Exception as e:
                st.error(f"Erro ao ler arquivo: {e}")

    # ── Listagem (Mobile First Feed) ──────────────────────────────────
    sec("🔍", f"Transações de {MESES_PT[mes_sel]}")
    
    # Barra de busca e controle
    col_busca, col_gerenciar = st.columns([2, 1])
    with col_busca:
        busca = st.text_input("Buscar...", placeholder="Filtrar por descrição...", key="busca_tx", label_visibility="collapsed")
    
    txs = get_transacoes_mes(conn, prefixo_mes, busca)

    with col_gerenciar:
        if txs.empty:
            tx_opcoes = []
        else:
            tx_opcoes = txs.to_dict('records')
            
        tx_sel_id = st.selectbox(
            "Gerenciar", 
            options=[None] + [t['id'] for t in tx_opcoes],
            format_func=lambda x: "✏️ Editar / Excluir" if x is None else f"{next(t['descricao'] for t in tx_opcoes if t['id'] == x)} ({next(fmt(t['valor']) for t in tx_opcoes if t['id'] == x)})",
            label_visibility="collapsed"
        )
    
    if tx_sel_id is not None:
        tx_sel = next(t for t in tx_opcoes if t['id'] == tx_sel_id)
        st.markdown(f"**Ação para:** {tx_sel['descricao']} - {fmt(tx_sel['valor'])}")
        c1, c2 = st.columns(2)
        if c1.button("🗑️ Excluir Transação", type="primary", use_container_width=True):
             conn.execute("DELETE FROM transacoes WHERE id=?", (tx_sel_id,))
             conn.commit()
             from core.models import clear_cache_transacoes
             clear_cache_transacoes()
             st.toast("Removida com sucesso!")
             st.rerun()
        if c2.button("✏️ Editar Transação", use_container_width=True):
             st.info("Para editar, exclua a transação e crie novamente (a funcionalidade de edição completa será adicionada em breve).")

    if txs.empty:
        st.info("Nenhuma transação encontrada.")
    else:
        # Totalizador visual
        tot_rec = txs[txs['tipo'] == 'receita']['valor'].sum()
        tot_desp = txs[txs['tipo'] == 'despesa']['valor'].sum()
        tot_saldo = tot_rec - tot_desp
        
        st.markdown(f"""
        <div style="display:flex; justify-content:space-around; padding: 0.8rem; background: linear-gradient(135deg, rgba(22,27,38,0.7), rgba(11,14,20,0.8)); border-radius: 12px; margin-bottom: 1.5rem; border: 1px solid rgba(255,255,255,0.03);">
            <div style="text-align:center;">
                <div style="font-size:0.65rem; color:#8b95a5; text-transform:uppercase;">Receitas</div>
                <div style="font-weight:700; color:#00d4aa;">{fmt(tot_rec)}</div>
            </div>
            <div style="text-align:center;">
                <div style="font-size:0.65rem; color:#8b95a5; text-transform:uppercase;">Despesas</div>
                <div style="font-weight:700; color:#ff4b6e;">{fmt(tot_desp)}</div>
            </div>
            <div style="text-align:center;">
                <div style="font-size:0.65rem; color:#8b95a5; text-transform:uppercase;">Balanço</div>
                <div style="font-weight:700; color:{'#00d4aa' if tot_saldo >= 0 else '#ff4b6e'};">{fmt(tot_saldo)}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Agrupar por data (dia) para o Feed
        txs['data_formatada'] = pd.to_datetime(txs['data']).dt.strftime('%Y-%m-%d')
        datas_unicas = sorted(txs['data_formatada'].unique(), reverse=True)

        html_feed = "<div class='tx-feed-container'>"
        for dt in datas_unicas:
            dt_obj = datetime.strptime(dt, '%Y-%m-%d')
            mes_nome = MESES_PT[dt_obj.month][:3].upper()
            cabecalho_dia = f"{dt_obj.day:02d} DE {mes_nome}"
            
            # Adiciona o cabeçalho do dia
            html_feed += f'<div class="day-header">{cabecalho_dia}</div>'

            txs_dia = txs[txs['data_formatada'] == dt]
            for _, row in txs_dia.iterrows():
                is_inc = row['tipo'] == 'receita'
                bg_class = 'inc-bg' if is_inc else 'exp-bg'
                amount_class = 'inc' if is_inc else 'exp'
                sinal = "+" if is_inc else ""
                icone = row['ci'] if pd.notna(row['ci']) else '📌'
                cat_nome = row['cat'] if pd.notna(row['cat']) else 'Sem categoria'
                conta_nome = row['conta'] if pd.notna(row['conta']) else 'Sem conta'
                
                # HTML minificado em uma única linha para evitar o parser de Markdown do Streamlit
                html_feed += f'<div class="tx-item"><div class="tx-left"><div class="tx-cat-icon {bg_class}">{icone}</div><div><div class="tx-desc">{html.escape(str(row["descricao"]))}</div><div class="tx-meta">{html.escape(str(conta_nome))} &bull; {html.escape(str(cat_nome))}</div></div></div><div class="tx-amount {amount_class}">{sinal} {fmt(row["valor"])}</div></div>'
        
        html_feed += "</div>"
        st.html(html_feed)
