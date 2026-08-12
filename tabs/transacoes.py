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
                    st.success(f"✅ Transação salva!" if qtd_parcelas == 1 else f"✅ Compra parcelada salva em {qtd_parcelas}x!")
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
                    st.success(f"✅ {inseridos} transações importadas com sucesso!")
                    st.rerun()
            except Exception as e:
                st.error(f"Erro ao ler arquivo: {e}")

    # ── Listagem (Com AgGrid) ─────────────────────────────────────────
    sec("🔍", f"Transações de {MESES_PT[mes_sel]}")
    busca = st.text_input("Buscar...", placeholder="Filtrar por descrição...", key="busca_tx")
    txs = get_transacoes_mes(conn, prefixo_mes, busca)

    if txs.empty:
        st.info("Nenhuma transação.")
    else:
        from st_aggrid import AgGrid, GridOptionsBuilder, ColumnsAutoSizeMode

        # Formatar colunas para exibição
        df_exibicao = txs.copy()
        
        # Juntar ícone com categoria e conta
        df_exibicao['Categoria'] = df_exibicao.apply(lambda x: f"{x['ci'] or '📌'} {x['cat']}" if x['cat'] else "", axis=1)
        df_exibicao['Conta'] = df_exibicao['conta']
        df_exibicao['Data'] = df_exibicao['data']
        df_exibicao['Descrição'] = df_exibicao['descricao']
        df_exibicao['Valor'] = df_exibicao['valor']
        df_exibicao['Tipo'] = df_exibicao.apply(lambda x: '🟢 Receita' if x['tipo'] == 'receita' else '🔴 Despesa', axis=1)
        df_exibicao['Tags'] = df_exibicao['tags_str']
        
        colunas_mostrar = ['Data', 'Tipo', 'Descrição', 'Valor', 'Categoria', 'Conta', 'Tags']
        df_grid = df_exibicao[colunas_mostrar]

        gb = GridOptionsBuilder.from_dataframe(df_grid)
        gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=15)
        gb.configure_default_column(resizable=True, filterable=True, sortable=True)
        gb.configure_column("Valor", type=["numericColumn", "numberColumnFilter"], valueFormatter="x.toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'})")
        gb.configure_selection('single', use_checkbox=True)
        
        gridOptions = gb.build()

        st.markdown("<style>.ag-theme-streamlit { font-family: 'Inter', sans-serif; }</style>", unsafe_allow_html=True)
        
        grid_response = AgGrid(
            df_grid,
            gridOptions=gridOptions,
            update_mode='MODEL_CHANGED',
            fit_columns_on_grid_load=True,
            theme='streamlit',
            columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS
        )
        
        # Ações baseadas na seleção
        selecionados = grid_response.get('selected_rows', [])
        if selecionados and len(selecionados) > 0:
            sel_idx = selecionados[0]['_selectedRowNodeInfo']['nodeRowIndex']
            tx_id = int(txs.iloc[sel_idx]['id'])
            
            st.markdown("---")
            st.markdown(f"**Ação para:** {selecionados[0]['Descrição']}")
            col1, col2, _ = st.columns([1, 1, 4])
            with col1:
                if st.button("✏️ Editar", key="btn_edit", width='stretch'):
                    st.session_state["tx_editando"] = tx_id
                    st.rerun()
            with col2:
                if st.button("🗑️ Excluir", type="primary", key="btn_del", width='stretch'):
                    conn.execute("DELETE FROM transacoes WHERE id=?", (tx_id,))
                    conn.commit()
                    st.success("Removida!")
                    st.rerun()
                    
            if st.session_state.get("tx_editando") == tx_id:
                # Formulário de edição rápida
                st.info("Para editar, exclua e crie novamente (ou implementaremos edição em breve).")
                if st.button("Cancelar Edição"):
                    st.session_state["tx_editando"] = None
                    st.rerun()
