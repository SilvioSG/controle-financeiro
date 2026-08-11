"""
tabs/metas.py — Aba de Metas Financeiras.
"""
import streamlit as st
import pandas as pd

from core.utils import fmt
from core.models import get_metas
from components.cards import sec


def render(ctx):
    """Renderiza a aba Metas."""
    conn = ctx["conn"]

    if st.session_state.pop("show_balloons", False):
        st.balloons()

    sec("🛡️", "Metas Financeiras")
    metas_df = get_metas(conn)

    if not metas_df.empty:
        for _, m in metas_df.iterrows():
            pct = min(m["valor_atual"] / m["valor_meta"], 1.0) * 100 if m["valor_meta"] > 0 else 0
            bc = "g-green" if pct >= 80 else ("g-amber" if pct >= 40 else "g-red")
            rest = max(m["valor_meta"] - m["valor_atual"], 0)
            cm2, ca2 = st.columns([8, 2])
            with cm2:
                st.markdown(f"""
                    <div class="goal-card">
                        <div style="display:flex;justify-content:space-between;align-items:center;">
                            <span style="color:#f0f2f5;font-weight:700;">🎯 {m['nome']}</span>
                            <span style="color:#f0f2f5;font-weight:800;font-size:1.1rem;">{pct:.0f}%</span>
                        </div>
                        <div class="goal-bar-bg"><div class="goal-bar-fill {bc}" style="width:{pct}%;"></div></div>
                        <div style="display:flex;justify-content:space-between;">
                            <span style="color:#8b95a5;font-size:0.72rem;">Guardado: {fmt(m['valor_atual'])}</span>
                            <span style="color:#8b95a5;font-size:0.72rem;">Meta: {fmt(m['valor_meta'])}</span>
                        </div>
                        <div style="color:#5a6478;font-size:0.68rem;margin-top:0.3rem;">Faltam {fmt(rest)}</div>
                    </div>
                """, unsafe_allow_html=True)
            with ca2:
                av = st.number_input("Valor (R$)", min_value=0.0, step=50.0, format="%.2f", key=f"av_{m['id']}")
                a1, a2 = st.columns(2)
                with a1:
                    if st.button("➕", key=f"ba_{m['id']}"):
                        if av > 0:
                            conn.execute("UPDATE metas SET valor_atual=valor_atual+? WHERE id=?", (av, m["id"]))
                            conn.commit()
                            
                            novo_valor = m["valor_atual"] + av
                            if m["valor_atual"] < m["valor_meta"] and novo_valor >= m["valor_meta"]:
                                st.session_state["show_balloons"] = True
                                
                            st.rerun()
                with a2:
                    if st.button("🗑️", key=f"dm_{m['id']}"):
                        conn.execute("DELETE FROM metas WHERE id=?", (m["id"],))
                        conn.commit()
                        st.rerun()
    else:
        st.info("Nenhuma meta.")

    # ── Nova Meta ─────────────────────────────────────────────────────
    sec("➕", "Nova Meta")
    with st.form("form_meta", clear_on_submit=True):
        m1, m2, m3 = st.columns(3)
        with m1:
            nm2 = st.text_input("Nome", placeholder="Ex: Reserva de Emergência")
        with m2:
            vm = st.number_input("Valor da meta (R$)", min_value=0.01, step=100.0, format="%.2f")
        with m3:
            va = st.number_input("Valor já guardado (R$)", min_value=0.0, step=100.0, format="%.2f")
        if st.form_submit_button("💾 Criar Meta", use_container_width=True):
            if nm2.strip() and vm > 0:
                conn.execute("INSERT INTO metas (nome,valor_meta,valor_atual) VALUES (?,?,?)", (nm2.strip(), vm, va))
                conn.commit()
                st.success("✅ Criada!")
                st.rerun()

    # ── Calculadora de Reserva de Emergência ──────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    sec("🧮", "Calculadora de Reserva de Emergência")
    rc1, rc2 = st.columns(2)
    with rc1:
        custo = st.number_input("Custo mensal (R$)", min_value=0.0, step=100.0, format="%.2f", key="calc_r")
    with rc2:
        guardado = st.number_input("Já guardado (R$)", min_value=0.0, step=100.0, format="%.2f", key="calc_g")

    if custo > 0:
        r6 = custo * 6
        r12 = custo * 12
        pct6 = min(guardado / r6, 1.0) * 100 if r6 > 0 else 0
        pct12 = min(guardado / r12, 1.0) * 100 if r12 > 0 else 0
        falta6 = max(r6 - guardado, 0)
        falta12 = max(r12 - guardado, 0)

        st.markdown(f"""
            <div class="glass-card">
                <div style="display:flex;gap:2rem;flex-wrap:wrap;">
                    <div style="flex:1;min-width:200px;">
                        <div style="font-size:0.75rem;color:#8b95a5;text-transform:uppercase;">Meta 6 meses</div>
                        <div style="font-size:1.3rem;font-weight:800;color:#00d4aa;">{fmt(r6)}</div>
                        <div class="goal-bar-bg" style="margin:0.4rem 0;"><div class="goal-bar-fill g-green" style="width:{pct6}%;"></div></div>
                        <div style="font-size:0.72rem;color:#8b95a5;">Progresso: {pct6:.0f}% · Faltam {fmt(falta6)}</div>
                    </div>
                    <div style="flex:1;min-width:200px;">
                        <div style="font-size:0.75rem;color:#8b95a5;text-transform:uppercase;">Meta 12 meses</div>
                        <div style="font-size:1.3rem;font-weight:800;color:#4e8cff;">{fmt(r12)}</div>
                        <div class="goal-bar-bg" style="margin:0.4rem 0;"><div class="goal-bar-fill g-amber" style="width:{pct12}%;"></div></div>
                        <div style="font-size:0.72rem;color:#8b95a5;">Progresso: {pct12:.0f}% · Faltam {fmt(falta12)}</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        if falta6 > 0:
            for meses_alvo in [6, 12, 24]:
                aporte_mensal = falta6 / meses_alvo
                st.markdown(f"""
                    <div style="display:inline-flex;align-items:center;gap:0.5rem;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);border-radius:8px;padding:0.4rem 0.8rem;margin:0.15rem;">
                        <span style="font-size:0.75rem;color:#8b95a5;">Em {meses_alvo} meses:</span>
                        <span style="font-size:0.85rem;font-weight:700;color:#f0f2f5;">{fmt(aporte_mensal)}/mês</span>
                    </div>
                """, unsafe_allow_html=True)

        st.markdown(f"""
            <div class="insight-card" style="margin-top:0.8rem;">
                <span class="insight-icon">💡</span>
                <div>
                    <div class="insight-text">Invista sua reserva em <strong>Tesouro Selic</strong> ou <strong>CDB com liquidez diária 100% CDI</strong>.
                    São as opções mais seguras e com resgate rápido para emergências.</div>
                    <div class="insight-label">Onde investir a reserva</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
