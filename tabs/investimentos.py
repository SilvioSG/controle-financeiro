"""
tabs/investimentos.py — Aba de Investimentos e simulador.
"""
import streamlit as st
import plotly.graph_objects as go

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
                        import google.genai as genai
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

    # ── Flowchart Onde Investir ───────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("🗺️ Mapa: Onde Investir?", expanded=False):
        st.markdown("""
        <div style="font-family: 'Inter', sans-serif; max-width: 700px; margin: 0 auto; color: var(--text);">
            <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); border-radius: 12px; padding: 1.5rem; position: relative;">
                
                <!-- Passo 1 -->
                <div style="text-align: center; margin-bottom: 2rem;">
                    <div style="display:inline-block; background: var(--purple); color: #fff; padding: 0.5rem 1rem; border-radius: 20px; font-weight: 700; margin-bottom: 0.5rem;">1. Você tem dívidas caras? (Cartão, Cheque Especial)</div>
                    <div style="display: flex; justify-content: center; gap: 4rem; margin-top: 0.5rem;">
                        <div style="text-align: center;">
                            <div style="font-weight: 700; color: var(--red);">SIM</div>
                            <div>⬇️</div>
                            <div style="background: rgba(255,75,110,0.1); border: 1px solid var(--red); color: var(--red); padding: 0.5rem; border-radius: 8px; font-size: 0.8rem; margin-top: 0.5rem;">Pague as dívidas PRIMEIRO.<br>Nenhum investimento rende<br>mais que os juros do cartão!</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-weight: 700; color: var(--green);">NÃO</div>
                            <div>⬇️</div>
                            <div style="font-size: 0.8rem; margin-top: 0.5rem; color: var(--text2);">Siga para o passo 2</div>
                        </div>
                    </div>
                </div>
                
                <hr style="border-color: rgba(255,255,255,0.05); margin: 2rem 0;">
                
                <!-- Passo 2 -->
                <div style="text-align: center; margin-bottom: 2rem;">
                    <div style="display:inline-block; background: var(--blue); color: #fff; padding: 0.5rem 1rem; border-radius: 20px; font-weight: 700; margin-bottom: 0.5rem;">2. Você tem Reserva de Emergência? (6 meses de gastos)</div>
                    <div style="display: flex; justify-content: center; gap: 4rem; margin-top: 0.5rem;">
                        <div style="text-align: center;">
                            <div style="font-weight: 700; color: var(--red);">NÃO</div>
                            <div>⬇️</div>
                            <div style="background: rgba(78,140,255,0.1); border: 1px solid var(--blue); color: #4e8cff; padding: 0.5rem; border-radius: 8px; font-size: 0.8rem; margin-top: 0.5rem;">Monte a Reserva!<br>Onde: <b>Tesouro Selic</b> ou<br><b>CDB 100% CDI Liquidez Diária</b>.</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-weight: 700; color: var(--green);">SIM</div>
                            <div>⬇️</div>
                            <div style="font-size: 0.8rem; margin-top: 0.5rem; color: var(--text2);">Siga para o passo 3</div>
                        </div>
                    </div>
                </div>
                
                <hr style="border-color: rgba(255,255,255,0.05); margin: 2rem 0;">
                
                <!-- Passo 3 -->
                <div style="text-align: center;">
                    <div style="display:inline-block; background: var(--green); color: #0b0e14; padding: 0.5rem 1rem; border-radius: 20px; font-weight: 700; margin-bottom: 0.5rem;">3. Qual o prazo do seu objetivo?</div>
                    <div style="display: flex; justify-content: center; flex-wrap: wrap; gap: 1rem; margin-top: 0.5rem;">
                        <div style="flex:1; min-width: 150px; background: rgba(255,255,255,0.02); padding: 1rem; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1);">
                            <div style="font-weight: 700; color: var(--amber); margin-bottom: 0.5rem;">Curto Prazo<br><span style="font-size:0.7rem;font-weight:400;">(Até 2 anos)</span></div>
                            <div style="font-size: 0.8rem; color: var(--text2);">Viagens, comprar carro.</div>
                            <div style="font-size: 0.85rem; font-weight: 700; margin-top: 0.5rem; color: #fff;">Onde investir:</div>
                            <div style="font-size: 0.8rem; color: var(--text3);">LCI/LCA, CDB Prefixado, Tesouro Prefixado.</div>
                        </div>
                        <div style="flex:1; min-width: 150px; background: rgba(255,255,255,0.02); padding: 1rem; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1);">
                            <div style="font-weight: 700; color: var(--green-glow); margin-bottom: 0.5rem;">Médio Prazo<br><span style="font-size:0.7rem;font-weight:400;">(3 a 5 anos)</span></div>
                            <div style="font-size: 0.8rem; color: var(--text2);">Comprar imóvel, casar.</div>
                            <div style="font-size: 0.85rem; font-weight: 700; margin-top: 0.5rem; color: #fff;">Onde investir:</div>
                            <div style="font-size: 0.8rem; color: var(--text3);">Tesouro IPCA+ (curto), Fundos Multimercado, CDBs longos.</div>
                        </div>
                        <div style="flex:1; min-width: 150px; background: rgba(255,255,255,0.02); padding: 1rem; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1);">
                            <div style="font-weight: 700; color: #a855f7; margin-bottom: 0.5rem;">Longo Prazo<br><span style="font-size:0.7rem;font-weight:400;">(5+ anos)</span></div>
                            <div style="font-size: 0.8rem; color: var(--text2);">Aposentadoria, independência.</div>
                            <div style="font-size: 0.85rem; font-weight: 700; margin-top: 0.5rem; color: #fff;">Onde investir:</div>
                            <div style="font-size: 0.8rem; color: var(--text3);">Tesouro IPCA+ (longo), Ações, FIIs, BDRs, ETFs (IVVB11).</div>
                        </div>
                    </div>
                </div>
                
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Simulador Side-by-Side ─────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    sec("⚖️", "Comparador de Investimentos (Side-by-Side)")
    st.caption("Compare lado a lado duas opções de renda fixa.")
    
    col_input1, col_input2, col_input3 = st.columns(3)
    with col_input1:
        capital = st.number_input("💰 Valor inicial (R$)", min_value=0.0, value=1000.0, step=100.0, format="%.2f", key="cap_sim")
    with col_input2:
        aporte = st.number_input("📥 Aporte mensal (R$)", min_value=0.0, value=500.0, step=50.0, format="%.2f", key="apo_sim")
    with col_input3:
        prazo = st.number_input("📅 Prazo (meses)", min_value=1, max_value=360, value=24, step=12, key="prz_sim")

    st.markdown("---")
    
    opcoes = {
        "🏛️ Tesouro Selic (~14,25% a.a.)": 14.25,
        "🏦 CDB 100% CDI (~14,15% a.a.)": 14.15,
        "🏦 CDB 120% CDI (~17% a.a.)": 17.0,
        "🏠 LCI/LCA 90% CDI (isento IR)": 12.7,
        "💰 Poupança (~7,5% a.a.)": 7.5,
    }
    
    col_op1, col_op2 = st.columns(2)
    with col_op1:
        st.markdown("**Opção A**")
        opcao_a = st.selectbox("Escolha", list(opcoes.keys()), index=0, key="op_a", label_visibility="collapsed")
        taxa_a = opcoes[opcao_a]
        is_lci_a = "LCI" in opcao_a
        
    with col_op2:
        st.markdown("**Opção B**")
        opcao_b = st.selectbox("Escolha", list(opcoes.keys()), index=4, key="op_b", label_visibility="collapsed")
        taxa_b = opcoes[opcao_b]
        is_lci_b = "LCI" in opcao_b

    if (capital > 0 or aporte > 0) and prazo > 0:
        sim_a = simular_investimento(capital, aporte, prazo, taxa_a)
        if is_lci_a:
            sim_a["ir"] = 0; sim_a["aliquota"] = 0; sim_a["liquido"] = sim_a["bruto"]
            
        sim_b = simular_investimento(capital, aporte, prazo, taxa_b)
        if is_lci_b:
            sim_b["ir"] = 0; sim_b["aliquota"] = 0; sim_b["liquido"] = sim_b["bruto"]

        # Mostrar Comparativo
        diff = sim_a['liquido'] - sim_b['liquido']
        vencedor = "Opção A" if diff > 0 else "Opção B" if diff < 0 else "Empate"
        
        st.markdown(f"""
            <div style="text-align:center; padding: 1rem; background: rgba(0,212,170,0.05); border: 1px solid rgba(0,212,170,0.2); border-radius: 12px; margin: 1rem 0;">
                <div style="font-size: 0.9rem; color: var(--text2);">A melhor opção é <b>{vencedor}</b></div>
                <div style="font-size: 1.2rem; font-weight: 700; color: #00d4aa; margin-top: 0.2rem;">Diferença de {fmt(abs(diff))}</div>
            </div>
        """, unsafe_allow_html=True)
        
        # Tabela Comparativa Visual
        c_r1, c_r2 = st.columns(2)
        with c_r1:
            st.markdown(f"""
                <div class="glass-card" style="border-left: 4px solid {'#00d4aa' if diff >= 0 else '#8b95a5'};">
                    <div style="font-size: 0.8rem; font-weight: 700; color: #fff; margin-bottom: 0.5rem;">{opcao_a}</div>
                    <div style="display:flex; justify-content:space-between; margin-bottom:0.2rem;">
                        <span style="font-size:0.75rem; color:var(--text2);">Investido:</span>
                        <span style="font-size:0.75rem; font-weight:600;">{fmt(sim_a['investido'])}</span>
                    </div>
                    <div style="display:flex; justify-content:space-between; margin-bottom:0.2rem;">
                        <span style="font-size:0.75rem; color:var(--text2);">Rend. Bruto:</span>
                        <span style="font-size:0.75rem; font-weight:600; color:var(--green);">{fmt(sim_a['rendimento'])}</span>
                    </div>
                    <div style="display:flex; justify-content:space-between; margin-bottom:0.5rem; padding-bottom:0.5rem; border-bottom: 1px solid rgba(255,255,255,0.05);">
                        <span style="font-size:0.75rem; color:var(--text2);">IR ({sim_a['aliquota']:.1f}%):</span>
                        <span style="font-size:0.75rem; font-weight:600; color:var(--red);">- {fmt(sim_a['ir'])}</span>
                    </div>
                    <div style="display:flex; justify-content:space-between; align-items:flex-end;">
                        <span style="font-size:0.8rem; text-transform:uppercase; color:var(--text3);">Líquido</span>
                        <span style="font-size:1.3rem; font-weight:800; color:#fff;">{fmt(sim_a['liquido'])}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
        with c_r2:
            st.markdown(f"""
                <div class="glass-card" style="border-left: 4px solid {'#00d4aa' if diff < 0 else '#8b95a5'};">
                    <div style="font-size: 0.8rem; font-weight: 700; color: #fff; margin-bottom: 0.5rem;">{opcao_b}</div>
                    <div style="display:flex; justify-content:space-between; margin-bottom:0.2rem;">
                        <span style="font-size:0.75rem; color:var(--text2);">Investido:</span>
                        <span style="font-size:0.75rem; font-weight:600;">{fmt(sim_b['investido'])}</span>
                    </div>
                    <div style="display:flex; justify-content:space-between; margin-bottom:0.2rem;">
                        <span style="font-size:0.75rem; color:var(--text2);">Rend. Bruto:</span>
                        <span style="font-size:0.75rem; font-weight:600; color:var(--green);">{fmt(sim_b['rendimento'])}</span>
                    </div>
                    <div style="display:flex; justify-content:space-between; margin-bottom:0.5rem; padding-bottom:0.5rem; border-bottom: 1px solid rgba(255,255,255,0.05);">
                        <span style="font-size:0.75rem; color:var(--text2);">IR ({sim_b['aliquota']:.1f}%):</span>
                        <span style="font-size:0.75rem; font-weight:600; color:var(--red);">- {fmt(sim_b['ir'])}</span>
                    </div>
                    <div style="display:flex; justify-content:space-between; align-items:flex-end;">
                        <span style="font-size:0.8rem; text-transform:uppercase; color:var(--text3);">Líquido</span>
                        <span style="font-size:1.3rem; font-weight:800; color:#fff;">{fmt(sim_b['liquido'])}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        # ── Gráfico de evolução comparativo ───────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        sec("📈", "Evolução do Patrimônio Lado a Lado")
        
        hist_a = sim_a["historico"]
        hist_b = sim_b["historico"]
        
        fig_inv = go.Figure()
        
        # Opção A
        fig_inv.add_trace(go.Scatter(
            x=[h["mes"] for h in hist_a], y=[h["saldo"] for h in hist_a],
            name="Opção A", mode="lines", line=dict(color="#00d4aa", width=2.5),
            fill="tozeroy", fillcolor="rgba(0,212,170,0.08)",
        ))
        
        # Opção B
        fig_inv.add_trace(go.Scatter(
            x=[h["mes"] for h in hist_b], y=[h["saldo"] for h in hist_b],
            name="Opção B", mode="lines", line=dict(color="#4e8cff", width=2.5),
            fill="tozeroy", fillcolor="rgba(78,140,255,0.05)",
        ))
        
        # Investido
        fig_inv.add_trace(go.Scatter(
            x=[h["mes"] for h in hist_a], y=[h["investido"] for h in hist_a],
            name="Investido", mode="lines", line=dict(color="#8b95a5", width=2, dash="dash"),
        ))
        
        fig_inv.update_layout(
            **PLOTLY_LAYOUT, height=350,
            xaxis=dict(title="Mês", showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.03)"),
            hovermode="x unified"
        )
        st.plotly_chart(fig_inv, key="inv_comp_chart", width='stretch')

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
                    • <strong style="color:#a855f7;">Melhor líquido curto/médio prazo</strong>
                </div>
            </div>
        """, unsafe_allow_html=True)
