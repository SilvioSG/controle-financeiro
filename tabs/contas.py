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
        st.markdown("""
            <div class="empty-state">
                <div class="empty-icon">🏦</div>
                <div class="empty-title">Nenhuma conta cadastrada</div>
                <div class="empty-desc">Crie sua primeira conta para começar a controlar suas finanças. Adicione abaixo!</div>
            </div>
        """, unsafe_allow_html=True)
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
            
            # Sparkline de 30 dias
            import datetime
            hoje = datetime.date.today()
            trinta_dias = hoje - datetime.timedelta(days=30)
            
            txs_spark = read_sql(
                "SELECT data, tipo, valor FROM transacoes WHERE conta_id=? AND data >= ? ORDER BY data ASC",
                conn, params=(c["id"], trinta_dias.strftime("%Y-%m-%d"))
            )
            
            spark_svg = ""
            if not txs_spark.empty:
                txs_spark["dia"] = pd.to_datetime(txs_spark["data"]).dt.date
                txs_spark["delta"] = txs_spark.apply(lambda r: r["valor"] if r["tipo"] == "receita" else -r["valor"], axis=1)
                daily = txs_spark.groupby("dia")["delta"].sum().reset_index()
                
                idx = pd.date_range(trinta_dias, hoje)
                daily.set_index(pd.to_datetime(daily["dia"]), inplace=True)
                daily = daily.reindex(idx, fill_value=0)
                
                cum_trend = daily["delta"].cumsum().tolist()
                
                if any(v != 0 for v in cum_trend):
                    max_s = max(cum_trend)
                    min_s = min(cum_trend)
                    range_s = max(max_s - min_s, 1)
                    
                    points = []
                    for i, v in enumerate(cum_trend):
                        x = i * (80 / max(len(cum_trend) - 1, 1))
                        y = 30 - ((v - min_s) / range_s) * 20
                        points.append(f"{x},{y}")
                    pts_str = " ".join(points)
                    
                    spark_color = "#00d4aa" if cum_trend[-1] >= cum_trend[0] else "#ff4b6e"
                    import base64
                    svg_raw = (
                        f'<svg xmlns="http://www.w3.org/2000/svg" width="80" height="35" viewBox="0 0 80 35">'
                        f'<polyline points="{pts_str}" fill="none" stroke="{spark_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
                        f'</svg>'
                    )
                    b64 = base64.b64encode(svg_raw.encode()).decode()
                    spark_svg = f"""
                    <div style="margin-left:auto; margin-right: 1.5rem; width:80px; height:35px;" title="Tendência 30 dias">
                        <img src="data:image/svg+xml;base64,{b64}" width="80" height="35">
                    </div>
                    """
            
            ca, cd = st.columns([12, 1])
            with ca:
                st.markdown(
                    f'<div class="account-card"><div class="acc-left">'
                    f'<div class="acc-icon-wrap" style="background:{bg};">{c["icone"]}</div>'
                    f'<div><div class="acc-name">{c["nome"]}</div>'
                    f'<div class="acc-type">{c["tipo"]}</div></div></div>'
                    f'{spark_svg}'
                    f'<div class="acc-balance" style="color:{cs2};">{fmt(s)}</div></div>',
                    unsafe_allow_html=True,
                )
            with cd:
                with st.popover("🗑️"):
                    st.write("Excluir conta e todas suas transações?")
                    if st.button("Confirmar", key=f"da_{c['id']}", type="primary"):
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
                    if st.button("Salvar", key=f"es_{c['id']}", type="primary", width='stretch'):
                        if en.strip():
                            conn.execute("UPDATE contas SET nome=? WHERE id=?", (en.strip(), c["id"]))
                            conn.commit()
                            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
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

    if st.button("💾 Criar Conta", width='stretch', type="primary"):
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
            
            if st.form_submit_button("Realizar Transferência", type="primary", width='stretch'):
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
                            "INSERT INTO transacoes (tipo,descricao,valor,data,categoria_id,conta_id,observacao,is_transferencia) VALUES (?,?,?,?,?,?,?,1)",
                            ("despesa", f"Transferência para {dest_nome.split(' ', 1)[1]}", valor_transf, data_transf.strftime("%Y-%m-%d"), cat_id_val, orig_id, obs_transf)
                        )
                        # 2. Entra no destino (Receita)
                        conn.execute(
                            "INSERT INTO transacoes (tipo,descricao,valor,data,categoria_id,conta_id,observacao,is_transferencia) VALUES (?,?,?,?,?,?,?,1)",
                            ("receita", f"Transferência de {orig_nome.split(' ', 1)[1]}", valor_transf, data_transf.strftime("%Y-%m-%d"), cat_id_val, dest_id, obs_transf)
                        )
                        conn.commit()
                        from core.models import clear_cache_transacoes
                        clear_cache_transacoes()
                        st.success("✅ Transferência realizada com sucesso!")
                        st.rerun()
                    else:
                        st.error("Nenhuma categoria encontrada para registrar a transferência.")
