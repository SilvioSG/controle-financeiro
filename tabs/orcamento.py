"""
tabs/orcamento.py — Aba de Orçamento mensal.
"""
import streamlit as st
import pandas as pd

from core.utils import fmt, MESES_PT
from core.models import get_orcamentos_mes, get_categorias_despesa, get_gastos_categorias_mes
from components.cards import sec


def render(ctx):
    """Renderiza a aba Orçamento."""
    conn = ctx["conn"]
    prefixo_mes = ctx["prefixo_mes"]
    mes_sel = ctx["mes_sel"]
    ano_sel = ctx["ano_sel"]
    saldo_total = ctx["saldo_total"]

    # ── Alocação Base Zero (Fase 3.1) ─────────────────────────────────
    sec("📊", f"Orçamento de {MESES_PT[mes_sel]}")
    orc_data = get_orcamentos_mes(conn, mes_sel, ano_sel)

    if not orc_data.empty:
        t_orc, t_gasto, t_rolagem = 0, 0, 0
        
        # Calcular meses anteriores para rolagem
        mes_ant = mes_sel - 1 if mes_sel > 1 else 12
        ano_ant = ano_sel if mes_sel > 1 else ano_sel - 1
        prefixo_ant = f"{ano_ant}-{mes_ant:02d}"
        
        orc_ant_data = get_orcamentos_mes(conn, mes_ant, ano_ant)
        orc_ant_dict = {o["categoria_id"]: o["valor_limite"] for _, o in orc_ant_data.iterrows()} if not orc_ant_data.empty else {}
        
        # Pré-calcular gastos do mês atual e do mês anterior
        gastos_atual_dict = get_gastos_categorias_mes(conn, prefixo_mes)
        gastos_ant_dict = get_gastos_categorias_mes(conn, prefixo_ant)
        
        for _, o in orc_data.iterrows():
            cid = o["categoria_id"]
            
            # Gasto atual
            g_atual = gastos_atual_dict.get(cid, 0)
            
            # Rolagem (Fase 3.2)
            valor_rolagem = 0
            if cid in orc_ant_dict:
                g_ant = gastos_ant_dict.get(cid, 0)
                sobra_ant = orc_ant_dict[cid] - g_ant
                if sobra_ant > 0:
                    valor_rolagem = sobra_ant
            
            limite_real = o["valor_limite"] + valor_rolagem
            pct = (g_atual / limite_real * 100) if limite_real > 0 else 0
            bar_cls = "safe" if pct < 80 else ("warn" if pct < 100 else "over")
            
            t_orc += o["valor_limite"]
            t_rolagem += valor_rolagem
            t_gasto += g_atual
            
            texto_rolagem = f" <span style='font-size:0.6rem; color:#00d4aa;'>(+{fmt(valor_rolagem)} rolado)</span>" if valor_rolagem > 0 else ""
            
            co_col, cd_col = st.columns([12, 1])
            with co_col:
                st.markdown(
                    f'<div class="budget-item"><div class="budget-header">'
                    f'<span class="budget-cat">{o["icone"]} {o["nome"]} '
                    f'{"✅" if pct < 80 else "⚠️" if pct < 100 else "🚨"}</span>'
                    f'<span class="budget-vals">{fmt(g_atual)} / {fmt(limite_real)}{texto_rolagem} ({pct:.0f}%)</span>'
                    f'</div><div class="budget-bar-bg"><div class="budget-bar-fill {bar_cls}" '
                    f'style="width:{min(pct, 100)}%;"></div></div></div>',
                    unsafe_allow_html=True,
                )
            with cd_col:
                if st.button("🗑️", key=f"do_{o['id']}"):
                    conn.execute("DELETE FROM orcamentos WHERE id=?", (o["id"],))
                    conn.commit()
                    st.rerun()

        rest_limite = (t_orc + t_rolagem) - t_gasto
        
        # Métrica Base Zero (Saldo Livre - Orçado)
        saldo_livre_orcar = saldo_total - t_orc
        cor_base_zero = "#00d4aa" if saldo_livre_orcar >= 0 else "#ff4b6e"
        
        st.markdown(f"""
            <div class="glass-card" style="margin-top:1rem; border-left: 4px solid {cor_base_zero};">
                <div style="font-size:0.75rem; color:#8b95a5; text-transform:uppercase; font-weight:700; margin-bottom:0.5rem;">🧠 Orçamento Base Zero</div>
                <div style="display:flex; justify-content:space-between; flex-wrap:wrap; gap:1rem;">
                    <div>
                        <div style="font-size:0.7rem; color:#5a6478;">Total na Conta Corrente</div>
                        <div style="font-size:1.2rem; font-weight:800; color:#f0f2f5;">{fmt(saldo_total)}</div>
                    </div>
                    <div>
                        <div style="font-size:0.7rem; color:#5a6478;">Já Alocado em Potes</div>
                        <div style="font-size:1.2rem; font-weight:800; color:#4e8cff;">{fmt(t_orc)}</div>
                    </div>
                    <div>
                        <div style="font-size:0.7rem; color:#5a6478;">Ainda Sem Nome (Livre)</div>
                        <div style="font-size:1.2rem; font-weight:800; color:{cor_base_zero};">{fmt(saldo_livre_orcar)}</div>
                    </div>
                </div>
            </div>
            
            <div class="glass-card" style="margin-top:0.5rem;">
                <div style="display:flex; justify-content:space-around; text-align:center;">
                    <div>
                        <div style="font-size:0.7rem; color:#8b95a5; text-transform:uppercase;">Limite c/ Rolagem</div>
                        <div style="font-size:1.1rem; font-weight:700; color:#4e8cff;">{fmt(t_orc + t_rolagem)}</div>
                    </div>
                    <div>
                        <div style="font-size:0.7rem; color:#8b95a5; text-transform:uppercase;">Total Gasto</div>
                        <div style="font-size:1.1rem; font-weight:700; color:#ff4b6e;">{fmt(t_gasto)}</div>
                    </div>
                    <div>
                        <div style="font-size:0.7rem; color:#8b95a5; text-transform:uppercase;">Restante nos Potes</div>
                        <div style="font-size:1.1rem; font-weight:700; color:{"#00d4aa" if rest_limite >= 0 else "#ff4b6e"};">{fmt(rest_limite)}</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    else:
        st.info("Nenhum orçamento. Adicione abaixo.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Definir Limite ────────────────────────────────────────────────
    sec("➕", "Definir Limite")
    cats_d = get_categorias_despesa(conn)
    if not cats_d.empty:
        with st.form("form_orc", clear_on_submit=True):
            fo1, fo2 = st.columns(2)
            with fo1:
                oo = {f"{r['icone']} {r['nome']}": r["id"] for _, r in cats_d.iterrows()}
                os_sel = st.selectbox("Categoria", list(oo.keys()))
                oid = oo[os_sel]
            with fo2:
                ov = st.number_input("Limite (R$)", min_value=1.0, step=50.0, format="%.2f")
            if st.form_submit_button("💾 Definir", width='stretch'):
                if getattr(conn, 'is_postgres', False):
                    conn.execute(
                        "INSERT INTO orcamentos (categoria_id,valor_limite,mes,ano) VALUES (?,?,?,?) ON CONFLICT (categoria_id, mes, ano) DO UPDATE SET valor_limite = EXCLUDED.valor_limite",
                        (oid, ov, mes_sel, ano_sel),
                    )
                else:
                    conn.execute(
                        "INSERT OR REPLACE INTO orcamentos (categoria_id,valor_limite,mes,ano) VALUES (?,?,?,?)",
                        (oid, ov, mes_sel, ano_sel),
                    )
                conn.commit()
                st.success("✅ Definido!")
                st.rerun()
