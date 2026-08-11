"""
tabs/investimentos.py — Aba de Investimentos e simulador.
"""
import streamlit as st
import plotly.graph_objects as go
import google.genai as genai

from core.utils import fmt, PLOTLY_LAYOUT
from components.cards import sec
from intelligence.simulator import simular_investimento


def render(ctx):
    """Renderiza a aba Investimentos."""
    conn = ctx["conn"]
    saldo_total = ctx["saldo_total"]
    saldo_reserva = ctx["saldo_reserva"]

    sec("💹", "Simulador de Investimentos")
    st.caption("Compare opções de renda fixa e veja quanto seu dinheiro pode render.")

    # ── IA Especialista ───────────────────────────────────────────────
    with st.expander("🤖 Consultar IA Especialista Financeiro (Gemini)", expanded=False):
        st.markdown("O assistente analisará seu saldo atual, sua reserva e suas metas para te dar conselhos super avançados e personalizados.")
        api_key = st.text_input(
            "Sua Chave de API do Google Gemini", type="password",
            key="gemini_key",
            help="Pegue sua chave gratuitamente no Google AI Studio (aistudio.google.com).",
        )

        if st.button("Gerar Análise Personalizada", type="primary", width='stretch'):
            if not api_key:
                st.error("Por favor, insira sua Chave de API para usar a Inteligência Artificial.")
            else:
                with st.spinner("A IA está analisando suas finanças. Isso pode levar alguns segundos..."):
                    try:
                        client = genai.Client(api_key=api_key)

                        metas_ativas = conn.execute("SELECT nome, valor_meta, valor_atual FROM metas").fetchall()
                        metas_str = ", ".join(
                            [f"{m[0]} (Alvo: {fmt(m[1])}, Atual: {fmt(m[2])})" for m in metas_ativas]
                        ) if metas_ativas else "Nenhuma meta cadastrada"

                        prompt = f"""
                        Atue como um consultor financeiro brasileiro sênior, altamente especializado e didático.
                        O usuário quer recomendações de como investir o dinheiro.
                        Aqui estão os dados financeiros ATUAIS do usuário:
                        - Saldo Livre na Conta Corrente: {fmt(saldo_total)}
                        - Valor Guardado na Reserva de Emergência: {fmt(saldo_reserva)}
                        - Metas Financeiras: {metas_str}
                        
                        Levando em conta o cenário atual de juros no Brasil:
                        1. Avalie rapidamente se a divisão do dinheiro (reserva vs conta corrente) está saudável.
                        2. Dê orientações CLARAS de onde ele deve investir o 'Saldo Livre' (ex: Tesouro Direto, CDBs específicos, FIIs, etc).
                        3. Dê uma dica estratégica para ele bater a meta dele mais rápido.
                        
                        Não seja genérico. Dê nomes aos produtos (ex: "CDB 110% CDI", "Tesouro IPCA+").
                        Responda em formato Markdown, usando emojis e destaque em negrito onde for importante. Seja encorajador!
                        """
                        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                        st.markdown(f'''
                        <div class="glass-card" style="border-left: 4px solid var(--purple); background: rgba(168,85,247,0.05); margin-top: 1rem;">
                            <h4 style="margin-top:0; color:var(--purple); display:flex; align-items:center; gap:0.5rem;">🤖 Consultor Financeiro Inteligente</h4>
                            <div style="font-size: 0.9rem; line-height: 1.6; color: var(--text);">
                                {response.text}
                            </div>
                        </div>
                        ''', unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"Erro na comunicação com a IA: {e}. Verifique sua chave de API e sua conexão.")

    # ── Dica de reserva ───────────────────────────────────────────────
    if saldo_reserva > 0:
        st.markdown(f"""
            <div class="insight-card" style="margin: 1rem 0 1.5rem 0; border-color: #4e8cff; background: rgba(78,140,255,0.05);">
                <span class="insight-icon">🛡️</span>
                <div>
                    <div class="insight-text" style="font-size: 0.9rem;">Você tem <strong>{fmt(saldo_reserva)}</strong> na sua <strong>Reserva de Emergência</strong>!</div>
                    <div class="insight-text" style="margin-top: 0.4rem;">Onde investir a reserva? O foco aqui não é ficar rico, mas sim <strong>segurança e disponibilidade imediata (liquidez diária)</strong>.<br>
                    <strong>Melhores opções:</strong><br>
                    • <strong>Tesouro Selic:</strong> O investimento mais seguro do Brasil. Rende a taxa Selic e o resgate cai no mesmo dia (ou D+1).<br>
                    • <strong>CDB 100% CDI (Liquidez Diária):</strong> Rende quase o mesmo que o Selic e geralmente o saque é instantâneo no seu banco (ex: caixinhas do Nubank, CDB Banco Inter).</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
            <div class="insight-card" style="margin: 1rem 0 1.5rem 0; border-color: #f59e0b; background: rgba(245,158,11,0.05);">
                <span class="insight-icon">⚠️</span>
                <div>
                    <div class="insight-text">Você ainda não declarou nenhum valor na sua <strong>Reserva de Emergência</strong>.</div>
                    <div class="insight-text" style="margin-top: 0.4rem;">Antes de arriscar em investimentos longos, construa sua reserva (idealmente 6x seus custos mensais). Guarde-a sempre no <strong>Tesouro Selic</strong> ou <strong>CDB 100% CDI de Liquidez Diária</strong> para ter o dinheiro na mão quando a emergência bater.</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    # ── Simulador ─────────────────────────────────────────────────────
    col_sim, col_res = st.columns([1, 1])
    with col_sim:
        capital = st.number_input("💰 Valor inicial (R$)", min_value=0.0, value=1000.0, step=100.0, format="%.2f")
        aporte = st.number_input("📥 Aporte mensal (R$)", min_value=0.0, value=500.0, step=50.0, format="%.2f")
        prazo = st.number_input("📅 Prazo (meses)", min_value=1, max_value=360, value=24, step=12)

        st.markdown("---")
        st.markdown("**📊 Opções de Investimento:**")
        opcoes = {
            "🏛️ Tesouro Selic (~14,25% a.a.)": 14.25,
            "🏦 CDB 100% CDI (~14,15% a.a.)": 14.15,
            "🏦 CDB 120% CDI (~17% a.a.)": 17.0,
            "🏠 LCI/LCA 90% CDI (isento IR)": 12.7,
            "💰 Poupança (~7,5% a.a.)": 7.5,
            "📝 Taxa personalizada": 0,
        }
        opcao = st.selectbox("Escolha", list(opcoes.keys()))
        if "personalizada" in opcao.lower():
            taxa = st.number_input("Taxa anual (%)", min_value=0.1, value=14.0, step=0.5)
        else:
            taxa = opcoes[opcao]
        is_lci = "LCI" in opcao

    with col_res:
        if taxa > 0 and (capital > 0 or aporte > 0):
            sim = simular_investimento(capital, aporte, prazo, taxa)
            if is_lci:
                sim["ir"] = 0
                sim["aliquota"] = 0
                sim["liquido"] = sim["bruto"]

            sec("📈", "Resultado da Simulação")

            col_r1, col_r2 = st.columns(2)
            with col_r1:
                st.markdown(f"""
                    <div class="glass-card" style="text-align:center;">
                        <div style="font-size:0.7rem;color:#8b95a5;text-transform:uppercase;">Valor Líquido</div>
                        <div style="font-size:1.5rem;font-weight:800;color:#00d4aa;">{fmt(sim['liquido'])}</div>
                    </div>
                """, unsafe_allow_html=True)
            with col_r2:
                st.markdown(f"""
                    <div class="glass-card" style="text-align:center;">
                        <div style="font-size:0.7rem;color:#8b95a5;text-transform:uppercase;">Rendimento Líquido</div>
                        <div style="font-size:1.5rem;font-weight:800;color:#4e8cff;">{fmt(sim['liquido'] - sim['investido'])}</div>
                    </div>
                """, unsafe_allow_html=True)

            st.markdown(f"""
                <div class="glass-card" style="margin-top:0.5rem;">
                    <div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:0.5rem;">
                        <div style="text-align:center;flex:1;"><div style="font-size:0.65rem;color:#8b95a5;">Total Investido</div><div style="font-size:0.9rem;font-weight:700;color:#f0f2f5;">{fmt(sim['investido'])}</div></div>
                        <div style="text-align:center;flex:1;"><div style="font-size:0.65rem;color:#8b95a5;">Rendimento Bruto</div><div style="font-size:0.9rem;font-weight:700;color:#f0f2f5;">{fmt(sim['rendimento'])}</div></div>
                        <div style="text-align:center;flex:1;"><div style="font-size:0.65rem;color:#8b95a5;">IR ({sim['aliquota']:.1f}%)</div><div style="font-size:0.9rem;font-weight:700;color:#ff4b6e;">- {fmt(sim['ir'])}</div></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

    # ── Gráfico de evolução ───────────────────────────────────────────
    if taxa > 0 and (capital > 0 or aporte > 0):
        st.markdown("<br>", unsafe_allow_html=True)
        sec("📈", "Evolução do Patrimônio")
        hist = sim["historico"]
        fig_inv = go.Figure()
        fig_inv.add_trace(go.Scatter(
            x=[h["mes"] for h in hist], y=[h["saldo"] for h in hist],
            name="Saldo", mode="lines", line=dict(color="#00d4aa", width=2.5),
            fill="tozeroy", fillcolor="rgba(0,212,170,0.08)",
        ))
        fig_inv.add_trace(go.Scatter(
            x=[h["mes"] for h in hist], y=[h["investido"] for h in hist],
            name="Investido", mode="lines", line=dict(color="#4e8cff", width=2, dash="dash"),
        ))
        fig_inv.update_layout(
            **PLOTLY_LAYOUT, height=300,
            xaxis=dict(title="Mês", showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.03)"),
        )
        st.plotly_chart(fig_inv, key="inv_chart")

    # ── Guia Rápido ───────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    sec("📚", "Guia Rápido de Investimentos")
    col_i1, col_i2, col_i3 = st.columns(3)
    with col_i1:
        st.markdown("""
            <div class="glass-card">
                <div style="font-size:1.3rem;margin-bottom:0.4rem;">🏛️</div>
                <div style="font-size:0.85rem;font-weight:700;color:#f0f2f5;">Tesouro Selic</div>
                <div style="font-size:0.72rem;color:#8b95a5;margin-top:0.3rem;">
                    • Mais seguro do país<br>
                    • Liquidez D+1<br>
                    • ~14,25% a.a. (2025)<br>
                    • IR regressivo (15-22,5%)<br>
                    • <strong style="color:#00d4aa;">Ideal para reserva</strong>
                </div>
            </div>
        """, unsafe_allow_html=True)
    with col_i2:
        st.markdown("""
            <div class="glass-card">
                <div style="font-size:1.3rem;margin-bottom:0.4rem;">🏦</div>
                <div style="font-size:0.85rem;font-weight:700;color:#f0f2f5;">CDB 100-120% CDI</div>
                <div style="font-size:0.72rem;color:#8b95a5;margin-top:0.3rem;">
                    • Protegido pelo FGC (até R$250k)<br>
                    • Liquidez diária ou no vencimento<br>
                    • ~14-17% a.a.<br>
                    • IR regressivo<br>
                    • <strong style="color:#4e8cff;">Bom rendimento</strong>
                </div>
            </div>
        """, unsafe_allow_html=True)
    with col_i3:
        st.markdown("""
            <div class="glass-card">
                <div style="font-size:1.3rem;margin-bottom:0.4rem;">🏠</div>
                <div style="font-size:0.85rem;font-weight:700;color:#f0f2f5;">LCI / LCA</div>
                <div style="font-size:0.72rem;color:#8b95a5;margin-top:0.3rem;">
                    • Isento de IR<br>
                    • Protegido pelo FGC<br>
                    • ~90% CDI líquido<br>
                    • Carência de 90 dias<br>
                    • <strong style="color:#a855f7;">Melhor líquido em prazo curto</strong>
                </div>
            </div>
        """, unsafe_allow_html=True)
