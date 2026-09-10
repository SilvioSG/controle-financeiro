"""
tabs/metas.py — Aba de Metas Financeiras.
Versão 2.0: Ring progress, estimativa de tempo, badges de conquista, calculadora melhorada.
"""
import streamlit as st
import pandas as pd

from core.utils import fmt
from core.models import get_metas
from components.cards import sec, ring_progress, badge_card
from components.tooltip_helper import get_tooltip


def render(ctx):
    """Renderiza a aba Metas."""
    conn = ctx["conn"]

    if st.session_state.pop("show_balloons", False):
        st.balloons()

    sec("🛡️", "Metas Financeiras", tooltip="reserva")
    metas_df = get_metas(conn)

    if not metas_df.empty:
        # Calcular média de economia mensal para estimativa
        desp_mes = ctx.get("desp_mes", 0)
        rec_mes = ctx.get("rec_mes", 0)
        simples_mes = ctx.get("simples_mes", 0)
        economia_mensal = max(0, rec_mes - desp_mes - simples_mes)

        for _, m in metas_df.iterrows():
            pct = min(m["valor_atual"] / m["valor_meta"], 1.0) * 100 if m["valor_meta"] > 0 else 0
            rest = max(m["valor_meta"] - m["valor_atual"], 0)
            
            # Cor baseada no progresso
            ring_color = "#00d4aa" if pct >= 80 else ("#f59e0b" if pct >= 40 else "#ff4b6e")
            
            # Estimativa de tempo
            tempo_est = ""
            if rest > 0 and economia_mensal > 0:
                meses_falta = rest / economia_mensal
                if meses_falta < 1:
                    tempo_est = "Menos de 1 mês!"
                elif meses_falta < 12:
                    tempo_est = f"~{meses_falta:.0f} meses"
                else:
                    anos = meses_falta / 12
                    tempo_est = f"~{anos:.1f} anos"
            elif rest <= 0:
                tempo_est = "🎉 Meta alcançada!"
            
            # Ícone inteligente baseado no nome da meta
            meta_icon = "🎯"
            nome_lower = m["nome"].lower()
            if any(w in nome_lower for w in ["viagem", "férias", "praia"]):
                meta_icon = "🏖️"
            elif any(w in nome_lower for w in ["carro", "moto", "veículo"]):
                meta_icon = "🚗"
            elif any(w in nome_lower for w in ["casa", "apartamento", "imóvel", "moradia"]):
                meta_icon = "🏠"
            elif any(w in nome_lower for w in ["reserva", "emergência"]):
                meta_icon = "🛡️"
            elif any(w in nome_lower for w in ["curso", "faculdade", "estudo"]):
                meta_icon = "📚"
            elif any(w in nome_lower for w in ["celular", "notebook", "pc", "computador"]):
                meta_icon = "📱"
            elif any(w in nome_lower for w in ["casamento"]):
                meta_icon = "💒"

            cm2, ca2 = st.columns([8, 2])
            with cm2:
                ring_html = ring_progress(pct, size=65, stroke=6, color=ring_color, label=f"{pct:.0f}%")
                
                st.markdown(f"""
                    <div class="goal-card" style="border-left:4px solid {ring_color};">
                        <div style="display:flex;align-items:center;gap:1rem;">
                            <div style="flex-shrink:0;">
                                {ring_html}
                            </div>
                            <div style="flex:1;min-width:0;">
                                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.3rem;">
                                    <span style="color:var(--text);font-weight:700;font-size:0.95rem;">{meta_icon} {m['nome']}</span>
                                </div>
                                <div class="goal-bar-bg"><div class="goal-bar-fill {'g-green' if pct >= 80 else ('g-amber' if pct >= 40 else 'g-red')}" style="width:{pct}%;"></div></div>
                                <div style="display:flex;justify-content:space-between;margin-top:0.3rem;">
                                    <span style="color:var(--text2);font-size:0.72rem;">Guardado: <strong style="color:var(--text);">{fmt(m['valor_atual'])}</strong></span>
                                    <span style="color:var(--text2);font-size:0.72rem;">Meta: <strong style="color:var(--text);">{fmt(m['valor_meta'])}</strong></span>
                                </div>
                                <div style="display:flex;justify-content:space-between;margin-top:0.2rem;">
                                    <span style="color:var(--text3);font-size:0.68rem;">Faltam {fmt(rest)}</span>
                                    <span style="color:{ring_color};font-size:0.68rem;font-weight:600;">{tempo_est}</span>
                                </div>
                            </div>
                        </div>
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
                    with st.popover("🗑️"):
                        st.write("Deseja excluir esta meta?")
                        if st.button("Confirmar", key=f"dm_{m['id']}", type="primary"):
                            conn.execute("DELETE FROM metas WHERE id=?", (m["id"],))
                            conn.commit()
                            st.rerun()
        
        # Metas 100% alcançadas — mostrar badges
        metas_completas = [m for _, m in metas_df.iterrows() if m["valor_atual"] >= m["valor_meta"]]
        if metas_completas:
            sec("🏆", "Metas Conquistadas!")
            badges_html = '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:0.5rem;">'
            for m in metas_completas:
                badges_html += badge_card("🏆", m["nome"], f"Meta de {fmt(m['valor_meta'])} atingida!", "#f59e0b")
            badges_html += '</div>'
            st.markdown(badges_html, unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

    else:
        st.markdown("""
            <div class="empty-state">
                <div class="empty-icon">🎯</div>
                <div class="empty-title">Sem metas ainda</div>
                <div class="empty-desc">Defina metas financeiras para se motivar a poupar! Ex: Reserva de Emergência, Viagem, Carro novo.</div>
            </div>
        """, unsafe_allow_html=True)

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
        if st.form_submit_button("💾 Criar Meta", width='stretch'):
            if nm2.strip() and vm > 0:
                conn.execute("INSERT INTO metas (nome,valor_meta,valor_atual) VALUES (?,?,?)", (nm2.strip(), vm, va))
                conn.commit()
                st.success("✅ Criada!")
                st.rerun()

    # ── Calculadora de Reserva de Emergência ──────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    sec("🧮", "Calculadora de Reserva de Emergência", tooltip="reserva")
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

        col_r6, col_r12 = st.columns(2)
        with col_r6:
            ring6 = ring_progress(pct6, size=80, stroke=7, color="#00d4aa", label=f"{pct6:.0f}%")
            st.markdown(f"""
                <div class="glass-card" style="text-align:center;">
                    <div style="font-size:0.75rem;color:var(--text2);text-transform:uppercase;margin-bottom:0.5rem;">Meta 6 meses</div>
                    {ring6}
                    <div style="font-size:1.2rem;font-weight:800;color:#00d4aa;margin-top:0.5rem;">{fmt(r6)}</div>
                    <div style="font-size:0.72rem;color:var(--text2);margin-top:0.3rem;">Faltam {fmt(falta6)}</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col_r12:
            ring12 = ring_progress(pct12, size=80, stroke=7, color="#4e8cff", label=f"{pct12:.0f}%")
            st.markdown(f"""
                <div class="glass-card" style="text-align:center;">
                    <div style="font-size:0.75rem;color:var(--text2);text-transform:uppercase;margin-bottom:0.5rem;">Meta 12 meses</div>
                    {ring12}
                    <div style="font-size:1.2rem;font-weight:800;color:#4e8cff;margin-top:0.5rem;">{fmt(r12)}</div>
                    <div style="font-size:0.72rem;color:var(--text2);margin-top:0.3rem;">Faltam {fmt(falta12)}</div>
                </div>
            """, unsafe_allow_html=True)

        if falta6 > 0:
            st.markdown("<br>", unsafe_allow_html=True)
            planos_html = '<div style="display:flex;gap:0.5rem;flex-wrap:wrap;justify-content:center;">'
            for meses_alvo in [6, 12, 24]:
                aporte_mensal = falta6 / meses_alvo
                planos_html += f"""
                <div class="glass-card" style="flex:1;min-width:150px;text-align:center;padding:0.8rem;">
                    <div style="font-size:0.68rem;color:var(--text3);text-transform:uppercase;">Em {meses_alvo} meses</div>
                    <div style="font-size:1rem;font-weight:800;color:var(--text);margin-top:0.2rem;">{fmt(aporte_mensal)}<span style="font-size:0.7rem;color:var(--text2);">/mês</span></div>
                </div>
                """
            planos_html += '</div>'
            st.markdown(planos_html, unsafe_allow_html=True)

        st.markdown(f"""
            <div class="insight-card" style="margin-top:0.8rem;">
                <span class="insight-icon">💡</span>
                <div>
                    <div class="insight-text">Invista sua reserva em <strong>Tesouro Selic</strong> ou <strong>CDB com liquidez diária 100% CDI</strong>.
                    São as opções mais seguras e com resgate rápido para emergências.{get_tooltip("tesouro_selic")}</div>
                    <div class="insight-label">Onde investir a reserva</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
