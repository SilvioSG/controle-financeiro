"""
tabs/transacoes.py — Aba de Transações (criar, listar, buscar, editar, importar CSV).
"""
import streamlit as st
import pandas as pd
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
            
        recorrente_tx = st.checkbox("🔄 Lançamento Recorrente (Repete todo mês)")

        if st.form_submit_button("💾 Salvar Transação", use_container_width=True, type="primary"):
            if desc_tx.strip() and valor_tx > 0 and cat_id and conta_id:
                rec_val = 1 if recorrente_tx else 0
                cursor = conn.execute(
                    "INSERT INTO transacoes (tipo,descricao,valor,data,categoria_id,conta_id,recorrente,observacao) "
                    "VALUES (?,?,?,?,?,?,?,?)",
                    (tipo_tx, desc_tx.strip(), valor_tx, data_tx.strftime("%Y-%m-%d"),
                     cat_id, conta_id, rec_val, obs_tx.strip()),
                )
                tx_id = cursor.lastrowid
                
                if tags_tx.strip():
                    tags_list = [t.strip().lower() for t in tags_tx.split(",") if t.strip()]
                    for tag_nome in set(tags_list):
                        conn.execute("INSERT OR IGNORE INTO tags (nome) VALUES (?)", (tag_nome,))
                        tag_id = conn.execute("SELECT id FROM tags WHERE nome = ?", (tag_nome,)).fetchone()[0]
                        conn.execute("INSERT INTO transacao_tags (transacao_id, tag_id) VALUES (?, ?)", (tx_id, tag_id))
                        
                aprender_categoria(conn, desc_tx, cat_id)
                conn.commit()
                st.success("✅ Transação salva!")
                st.rerun()
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

    # ── Listagem ──────────────────────────────────────────────────────
    sec("🔍", f"Transações de {MESES_PT[mes_sel]}")
    busca = st.text_input("Buscar...", placeholder="Filtrar por descrição...", key="busca_tx")
    txs = get_transacoes_mes(conn, prefixo_mes, busca)

    if txs.empty:
        st.info("Nenhuma transação.")
    else:
        cur_day = None
        for _, tx in txs.iterrows():
            if tx["data"] != cur_day:
                cur_day = tx["data"]
                st.markdown(f'<div class="day-header">📅 {fmt_data_pt(cur_day)}</div>', unsafe_allow_html=True)
            ii = tx["tipo"] == "receita"
            ct, ce, cd = st.columns([11, 1, 1])
            with ct:
                rec_badge = ' <span style="font-size:0.6rem;background:rgba(78,140,255,0.15);color:#4e8cff;padding:0.1rem 0.4rem;border-radius:6px;">🔄 Recorrente</span>' if tx.get("recorrente") else ""
                obs_html = f' <span style="font-size:0.65rem;color:#5a6478;">— {tx["observacao"]}</span>' if tx.get("observacao") else ""
                tags_html = ""
                if tx.get("tags_str"):
                    for tag in tx["tags_str"].split(","):
                        tags_html += f' <span style="font-size:0.55rem;background:rgba(255,255,255,0.08);color:#a0aec0;padding:0.15rem 0.35rem;border-radius:4px;margin-left:0.2rem;">#{tag.strip()}</span>'
                st.markdown(f"""<div class="tx-item"><div class="tx-left">
                    <div class="tx-cat-icon {'inc-bg' if ii else 'exp-bg'}">{tx['ci'] or '📌'}</div>
                    <div><div class="tx-desc">{tx['descricao']}{rec_badge}</div><div class="tx-meta">{tx['cat'] or ''} · {tx['conta'] or ''}{obs_html}{tags_html}</div></div>
                    </div><div class="tx-amount {'inc' if ii else 'exp'}">{'+'if ii else'-'} {fmt(tx['valor'])}</div></div>""", unsafe_allow_html=True)
            with ce:
                if st.button("✏️", key=f"ed_{tx['id']}"):
                    st.session_state[f"editing_{tx['id']}"] = not st.session_state.get(f"editing_{tx['id']}", False)
            with cd:
                if st.button("🗑️", key=f"dt_{tx['id']}"):
                    conn.execute("DELETE FROM transacoes WHERE id=?", (tx["id"],))
                    conn.commit()
                    st.rerun()

            # ── Edição inline (Fase 2.2) ──────────────────────────────
            if st.session_state.get(f"editing_{tx['id']}", False):
                with st.container():
                    st.markdown(
                        '<div style="background:rgba(78,140,255,0.05);border:1px solid rgba(78,140,255,0.15);'
                        'border-radius:12px;padding:1rem;margin-bottom:0.5rem;">',
                        unsafe_allow_html=True,
                    )
                    with st.form(f"edit_form_{tx['id']}"):
                        e1, e2 = st.columns(2)
                        with e1:
                            ed_desc = st.text_input("Descrição", value=tx["descricao"], key=f"ed_desc_{tx['id']}")
                        with e2:
                            ed_valor = st.number_input(
                                "Valor (R$)", min_value=0.01, value=float(tx["valor"]),
                                step=10.0, format="%.2f", key=f"ed_val_{tx['id']}",
                            )
                        e3, e4 = st.columns(2)
                        with e3:
                            try:
                                ed_data_val = datetime.strptime(tx["data"], "%Y-%m-%d").date()
                            except Exception:
                                ed_data_val = date.today()
                            ed_data = st.date_input("Data", value=ed_data_val, key=f"ed_data_{tx['id']}")
                        with e4:
                            if not categorias_df.empty:
                                cat_keys = list(co.keys())
                                current_cat_label = None
                                for label, cid in co.items():
                                    if cid == conn.execute(
                                        "SELECT categoria_id FROM transacoes WHERE id=?", (tx["id"],)
                                    ).fetchone()[0]:
                                        current_cat_label = label
                                        break
                                idx = cat_keys.index(current_cat_label) if current_cat_label in cat_keys else 0
                                ed_cat = st.selectbox("Categoria", cat_keys, index=idx, key=f"ed_cat_{tx['id']}")
                                ed_cat_id = co[ed_cat]
                            else:
                                ed_cat_id = None
                        ed_obs = st.text_input("Observação", value=tx.get("observacao", "") or "", key=f"ed_obs_{tx['id']}")

                        e_save, e_cancel = st.columns(2)
                        with e_save:
                            if st.form_submit_button("💾 Salvar", use_container_width=True, type="primary"):
                                if ed_desc.strip() and ed_valor > 0 and ed_cat_id:
                                    conn.execute(
                                        "UPDATE transacoes SET descricao=?, valor=?, data=?, categoria_id=?, observacao=? WHERE id=?",
                                        (ed_desc.strip(), ed_valor, ed_data.strftime("%Y-%m-%d"), ed_cat_id, ed_obs.strip(), tx["id"]),
                                    )
                                    conn.commit()
                                    st.session_state[f"editing_{tx['id']}"] = False
                                    st.success("✅ Atualizada!")
                                    st.rerun()
                        with e_cancel:
                            if st.form_submit_button("❌ Cancelar", use_container_width=True):
                                st.session_state[f"editing_{tx['id']}"] = False
                                st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
