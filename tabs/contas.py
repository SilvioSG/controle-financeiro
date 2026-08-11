"""
tabs/contas.py — Aba de Contas (listar, criar, editar, excluir).
"""
import streamlit as st
import pandas as pd
from datetime import date

from core.utils import fmt
from core.database import saldo_conta, read_sql
from components.cards import sec


def render(ctx):
    """Renderiza a aba Contas."""
    conn = ctx["conn"]

    sec("🏦", "Suas Contas")
    cl = read_sql("SELECT * FROM contas", conn)

    if cl.empty:
        st.info("Nenhuma conta.")
    else:
        for _, c in cl.iterrows():
            s = saldo_conta(conn, c["id"])
            cs2 = "#00d4aa" if s >= 0 else "#ff4b6e"
            bg_colors = {
                "Carteira": "rgba(245,158,11,0.15)",
                "Conta Corrente": "rgba(78,140,255,0.15)",
                "Poupança": "rgba(0,212,170,0.15)",
                "Cartão de Crédito": "rgba(168,85,247,0.15)",
            }
            bg = bg_colors.get(c["tipo"], "rgba(78,140,255,0.15)")
            ca, cd = st.columns([12, 1])
            with ca:
                st.markdown(
                    f'<div class="account-card"><div class="acc-left">'
                    f'<div class="acc-icon-wrap" style="background:{bg};">{c["icone"]}</div>'
                    f'<div><div class="acc-name">{c["nome"]}</div>'
                    f'<div class="acc-type">{c["tipo"]}</div></div></div>'
                    f'<div class="acc-balance" style="color:{cs2};">{fmt(s)}</div></div>',
                    unsafe_allow_html=True,
                )
            with cd:
                if st.button("🗑️", key=f"da_{c['id']}"):
                    conn.execute("DELETE FROM transacoes WHERE conta_id=?", (c["id"],))
                    conn.execute("DELETE FROM contas WHERE id=?", (c["id"],))
                    conn.commit()
                    st.rerun()

            with st.expander(f"✏️ Editar: {c['nome']}"):
                ce1, ce2 = st.columns([3, 1])
                with ce1:
                    en = st.text_input("Novo nome da conta", value=c["nome"], key=f"en_{c['id']}")
                with ce2:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("Salvar", key=f"es_{c['id']}", type="primary", use_container_width=True):
                        if en.strip():
                            conn.execute("UPDATE contas SET nome=? WHERE id=?", (en.strip(), c["id"]))
                            conn.commit()
                            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Transferência entre Contas (Fase 2.3) ─────────────────────────
    sec("🔄", "Transferência entre Contas")
    contas_transf = conn.execute(
        "SELECT id, nome, icone FROM contas WHERE tipo NOT IN ('Cartão de Crédito')"
    ).fetchall()
    if len(contas_transf) >= 2:
        with st.form("form_transf", clear_on_submit=True):
            ft1, ft2 = st.columns(2)
            with ft1:
                origem_opt = {f"{c[2]} {c[1]}": c[0] for c in contas_transf}
                sel_orig = st.selectbox("Conta Origem", list(origem_opt.keys()), key="transf_orig")
            with ft2:
                destino_opt = {f"{c[2]} {c[1]}": c[0] for c in contas_transf}
                sel_dest = st.selectbox("Conta Destino", list(destino_opt.keys()), key="transf_dest")
            ft3, ft4 = st.columns(2)
            with ft3:
                val_transf = st.number_input("Valor (R$)", min_value=0.01, step=50.0, format="%.2f", key="transf_val")
            with ft4:
                data_transf = st.date_input("Data", value=date.today(), key="transf_data")

            if st.form_submit_button("🔄 Transferir", use_container_width=True, type="primary"):
                id_orig = origem_opt[sel_orig]
                id_dest = destino_opt[sel_dest]
                if id_orig == id_dest:
                    st.error("Conta origem e destino devem ser diferentes.")
                elif val_transf > 0:
                    nome_orig = sel_orig.split(" ", 1)[1] if " " in sel_orig else sel_orig
                    nome_dest = sel_dest.split(" ", 1)[1] if " " in sel_dest else sel_dest
                    data_str = data_transf.strftime("%Y-%m-%d")
                    conn.execute(
                        "INSERT INTO transacoes (tipo,descricao,valor,data,conta_id) VALUES ('despesa',?,?,?,?)",
                        (f"Transferência para {nome_dest}", val_transf, data_str, id_orig),
                    )
                    conn.execute(
                        "INSERT INTO transacoes (tipo,descricao,valor,data,conta_id) VALUES ('receita',?,?,?,?)",
                        (f"Transferência de {nome_orig}", val_transf, data_str, id_dest),
                    )
                    conn.commit()
                    st.success(f"✅ Transferência de {fmt(val_transf)} realizada!")
                    st.rerun()
    else:
        st.info("Crie ao menos 2 contas para fazer transferências.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Nova Conta ────────────────────────────────────────────────────
    sec("➕", "Nova Conta")
    c1, c2 = st.columns(2)
    with c1:
        nc = st.text_input("Nome", placeholder="Ex: Nubank...")
    with c2:
        tc = st.selectbox("Tipo", ["Carteira", "Conta Corrente", "Poupança", "Cartão de Crédito", "Reserva de Emergência"])

    c3, c4 = st.columns(2)
    with c3:
        ic = st.selectbox("Ícone", ["👛", "🏦", "💳", "🏧", "💰", "🏠", "🚗", "📱"])

    if tc == "Cartão de Crédito":
        with c4:
            si = st.number_input("Limite do Cartão (R$)", step=100.0, format="%.2f")
        c5, c6 = st.columns(2)
        with c5:
            dfech = st.number_input("Dia de Fechamento", min_value=1, max_value=31, value=1)
        with c6:
            dvenc = st.number_input("Dia de Vencimento", min_value=1, max_value=31, value=10)
    else:
        with c4:
            si = st.number_input("Saldo Inicial (R$)", step=100.0, format="%.2f")
        dfech, dvenc = 1, 10

    if st.button("💾 Criar Conta", use_container_width=True, type="primary"):
        if nc.strip():
            if tc == "Cartão de Crédito":
                conn.execute(
                    "INSERT INTO contas (nome,tipo,icone,saldo_inicial,limite_cartao,dia_fechamento,dia_vencimento) "
                    "VALUES (?,?,?,?,?,?,?)",
                    (nc.strip(), tc, ic, 0, si, dfech, dvenc),
                )
            else:
                conn.execute(
                    "INSERT INTO contas (nome,tipo,icone,saldo_inicial) VALUES (?,?,?,?)",
                    (nc.strip(), tc, ic, si),
                )
            conn.commit()
            st.success("✅ Criada!")
            st.rerun()
        else:
            st.error("Informe o nome.")

    # ── Transferência entre Contas (Fase 2.3) ─────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    sec("🔄", "Transferência entre Contas")
    
    if cl.empty or len(cl) < 2:
        st.info("Você precisa ter pelo menos 2 contas para fazer transferências.")
    else:
        with st.form("form_transferencia", clear_on_submit=True):
            ct_opts = {f"{r['icone']} {r['nome']}": r["id"] for _, r in cl.iterrows()}
            
            c_orig, c_dest = st.columns(2)
            with c_orig:
                orig_nome = st.selectbox("Conta Origem (Sai o dinheiro)", list(ct_opts.keys()), key="orig")
            with c_dest:
                dest_nome = st.selectbox("Conta Destino (Entra o dinheiro)", list(ct_opts.keys()), key="dest")
                
            t_val, t_data = st.columns(2)
            with t_val:
                valor_transf = st.number_input("Valor a transferir (R$)", min_value=0.01, step=10.0, format="%.2f")
            with t_data:
                data_transf = st.date_input("Data da Transferência", value=date.today())
                
            obs_transf = st.text_input("Observação (opcional)", placeholder="Ex: Guardando reserva")
            
            if st.form_submit_button("Realizar Transferência", type="primary", use_container_width=True):
                orig_id = ct_opts[orig_nome]
                dest_id = ct_opts[dest_nome]
                
                if orig_id == dest_id:
                    st.error("A conta de origem não pode ser a mesma de destino.")
                else:
                    # Tentar achar a categoria de "Transferência", se não tiver, pega a primeira
                    cat_id_transf = conn.execute("SELECT id FROM categorias WHERE nome LIKE '%transf%' OR nome LIKE '%invest%' LIMIT 1").fetchone()
                    if not cat_id_transf:
                        cat_id_transf = conn.execute("SELECT id FROM categorias LIMIT 1").fetchone()
                        
                    cat_id_val = cat_id_transf[0] if cat_id_transf else None
                    
                    if cat_id_val:
                        # 1. Sai da origem (Despesa)
                        conn.execute(
                            "INSERT INTO transacoes (tipo,descricao,valor,data,categoria_id,conta_id,observacao) VALUES (?,?,?,?,?,?,?)",
                            ("despesa", f"Transferência para {dest_nome.split(' ', 1)[1]}", valor_transf, data_transf.strftime("%Y-%m-%d"), cat_id_val, orig_id, obs_transf)
                        )
                        # 2. Entra no destino (Receita)
                        conn.execute(
                            "INSERT INTO transacoes (tipo,descricao,valor,data,categoria_id,conta_id,observacao) VALUES (?,?,?,?,?,?,?)",
                            ("receita", f"Transferência de {orig_nome.split(' ', 1)[1]}", valor_transf, data_transf.strftime("%Y-%m-%d"), cat_id_val, dest_id, obs_transf)
                        )
                        conn.commit()
                        st.success("✅ Transferência realizada com sucesso!")
                        st.rerun()
                    else:
                        st.error("Nenhuma categoria encontrada para registrar a transferência.")
