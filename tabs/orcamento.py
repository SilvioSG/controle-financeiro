"""
tabs/orcamento.py — Aba de Orçamento mensal.
"""
import streamlit as st
import pandas as pd

from core.utils import fmt, MESES_PT
from core.models import get_orcamentos_mes, get_categorias_despesa
from components.cards import sec


def render(ctx):
    """Renderiza a aba Orçamento."""
    conn = ctx["conn"]
    prefixo_mes = ctx["prefixo_mes"]
    mes_sel = ctx["mes_sel"]
    ano_sel = ctx["ano_sel"]

    sec("📊", f"Orçamento de {MESES_PT[mes_sel]}")
    orc_data = get_orcamentos_mes(conn, mes_sel, ano_sel)

    if not orc_data.empty:
        t_orc, t_gasto = 0, 0
        for _, o in orc_data.iterrows():
            g = conn.execute(
                "SELECT COALESCE(SUM(valor),0) FROM transacoes "
                "WHERE tipo='despesa' AND categoria_id=? AND data LIKE ?",
                (o["categoria_id"], f"{prefixo_mes}%"),
            ).fetchone()[0]
            pct = (g / o["valor_limite"] * 100) if o["valor_limite"] > 0 else 0
            bar_cls = "safe" if pct < 80 else ("warn" if pct < 100 else "over")
            t_orc += o["valor_limite"]
            t_gasto += g
            co_col, cd_col = st.columns([12, 1])
            with co_col:
                st.markdown(
                    f'<div class="budget-item"><div class="budget-header">'
                    f'<span class="budget-cat">{o["icone"]} {o["nome"]} '
                    f'{"✅" if pct < 80 else "⚠️" if pct < 100 else "🚨"}</span>'
                    f'<span class="budget-vals">{fmt(g)} / {fmt(o["valor_limite"])} ({pct:.0f}%)</span>'
                    f'</div><div class="budget-bar-bg"><div class="budget-bar-fill {bar_cls}" '
                    f'style="width:{min(pct, 100)}%;"></div></div></div>',
                    unsafe_allow_html=True,
                )
            with cd_col:
                if st.button("🗑️", key=f"do_{o['id']}"):
                    conn.execute("DELETE FROM orcamentos WHERE id=?", (o["id"],))
                    conn.commit()
                    st.rerun()

        rest = t_orc - t_gasto
        st.markdown(
            f'<div class="glass-card" style="margin-top:1rem;">'
            f'<div style="display:flex;justify-content:space-around;text-align:center;">'
            f'<div><div style="font-size:0.7rem;color:#8b95a5;text-transform:uppercase;">Orçado</div>'
            f'<div style="font-size:1.1rem;font-weight:700;color:#4e8cff;">{fmt(t_orc)}</div></div>'
            f'<div><div style="font-size:0.7rem;color:#8b95a5;text-transform:uppercase;">Gasto</div>'
            f'<div style="font-size:1.1rem;font-weight:700;color:#ff4b6e;">{fmt(t_gasto)}</div></div>'
            f'<div><div style="font-size:0.7rem;color:#8b95a5;text-transform:uppercase;">Restante</div>'
            f'<div style="font-size:1.1rem;font-weight:700;color:{"#00d4aa" if rest >= 0 else "#ff4b6e"};">'
            f'{fmt(rest)}</div></div></div></div>',
            unsafe_allow_html=True,
        )
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
            if st.form_submit_button("💾 Definir", use_container_width=True):
                conn.execute(
                    "INSERT OR REPLACE INTO orcamentos (categoria_id,valor_limite,mes,ano) VALUES (?,?,?,?)",
                    (oid, ov, mes_sel, ano_sel),
                )
                conn.commit()
                st.success("✅ Definido!")
                st.rerun()
