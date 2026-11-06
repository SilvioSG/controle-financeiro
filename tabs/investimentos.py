"""
tabs/investimentos.py — Aba de Investimentos e simulador avançado com taxas do Banco Central.
"""
import streamlit as st
import plotly.graph_objects as go

from core.utils import fmt, PLOTLY_LAYOUT, get_taxas_bcb, get_gemini_api_key
from components.cards import sec
from intelligence.simulator import simular_investimento


def render(ctx):
    """Renderiza a aba Investimentos."""
    conn = ctx["conn"]
    saldo_total = ctx["saldo_total"]
    saldo_reserva = ctx["saldo_reserva"]

    # Buscar taxas reais do Banco Central (com fallback seguro)
    taxas_bcb = get_taxas_bcb()
    selic_atual = taxas_bcb["selic"]
    cdi_atual = taxas_bcb["cdi"]
    ipca_atual = taxas_bcb["ipca"]
    status_bcb = "🟢 Taxas BCB ao vivo" if taxas_bcb.get("online") else "📌 Taxas de Referência"

    sec("💹", "Central de Investimentos & Simulador")

    # ── Ticker de Indicadores de Mercado (Banco Central) ──────────────
    st.html(f"""
        <div style="display:flex;flex-wrap:wrap;gap:0.8rem;margin-bottom:1.2rem;">
            <div class="glass-card" style="flex:1;min-width:150px;padding:0.9rem 1.2rem;border-left:3px solid var(--green);">
                <div style="font-size:0.65rem;color:var(--text2);text-transform:uppercase;font-weight:600;">Taxa Selic Meta</div>
                <div style="font-size:1.35rem;font-weight:800;color:var(--green);">{selic_atual:.2f}% <span style="font-size:0.7rem;font-weight:500;">a.a.</span></div>
                <div style="font-size:0.6rem;color:var(--text3);">{status_bcb}</div>
            </div>
            <div class="glass-card" style="flex:1;min-width:150px;padding:0.9rem 1.2rem;border-left:3px solid var(--blue);">
                <div style="font-size:0.65rem;color:var(--text2);text-transform:uppercase;font-weight:600;">Taxa DI (CDI)</div>
                <div style="font-size:1.35rem;font-weight:800;color:var(--blue);">{cdi_atual:.2f}% <span style="font-size:0.7rem;font-weight:500;">a.a.</span></div>
                <div style="font-size:0.6rem;color:var(--text3);">Referência Renda Fixa</div>
            </div>
            <div class="glass-card" style="flex:1;min-width:150px;padding:0.9rem 1.2rem;border-left:3px solid var(--amber);">
                <div style="font-size:0.65rem;color:var(--text2);text-transform:uppercase;font-weight:600;">IPCA (Inflação 12m)</div>
                <div style="font-size:1.35rem;font-weight:800;color:var(--amber);">{ipca_atual:.2f}% <span style="font-size:0.7rem;font-weight:500;">a.a.</span></div>
                <div style="font-size:0.6rem;color:var(--text3);">Poder de compra</div>
            </div>
            <div class="glass-card" style="flex:1;min-width:150px;padding:0.9rem 1.2rem;border-left:3px solid var(--purple);">
                <div style="font-size:0.65rem;color:var(--text2);text-transform:uppercase;font-weight:600;">Juro Real Estimado</div>
                <div style="font-size:1.35rem;font-weight:800;color:var(--purple);">+{max(0.0, selic_atual - ipca_atual):.2f}% <span style="font-size:0.7rem;font-weight:500;">a.a.</span></div>
                <div style="font-size:0.6rem;color:var(--text3);">Acima da inflação</div>
            </div>
        </div>
    """)

    # ── IA Especialista ───────────────────────────────────────────────
    with st.expander("🤖 Consultar IA Especialista Financeiro (Gemini)", expanded=False):
        st.markdown("O assistente analisará seu saldo atual, sua reserva, as taxas atuais do Banco Central e suas metas para montar uma carteira recomendada.")
        saved_key = get_gemini_api_key()
        if saved_key:
            api_key = saved_key
            st.caption("🔑 Chave da API Gemini carregada automaticamente.")
        else:
            api_key = st.text_input(
                "Sua Chave de API do Google Gemini", type="password",
                key="gemini_key",
                help="Pegue sua chave gratuitamente no Google AI Studio (aistudio.google.com) ou salve em [gemini] api_key no secrets.toml.",
            )
            if api_key:
                st.session_state["gemini_api_key_shared"] = api_key

        if st.button("✨ Gerar Recomendação de Carteira", type="primary", use_container_width=True):
            if not api_key:
                st.error("Por favor, insira sua Chave de API para usar a Inteligência Artificial.")
            else:
                with st.spinner("A IA está analisando suas finanças e o cenário macroeconômico..."):
                    try:
                        import google.genai as genai
                        client = genai.Client(api_key=api_key)

                        metas_ativas = conn.execute("SELECT nome, valor_meta, valor_atual FROM metas").fetchall()
                        metas_str = ", ".join(
                            [f"{m[0]} (Alvo: {fmt(m[1])}, Atual: {fmt(m[2])})" for m in metas_ativas]
                        ) if metas_ativas else "Nenhuma meta cadastrada"

                        prompt = f"""
                        Atue como um planejador financeiro CFP brasileiro sênior e didático.
                        Dados financeiros ATUAIS do usuário:
                        - Saldo Livre no Mês: {fmt(saldo_total)}
                        - Valor Guardado na Reserva de Emergência: {fmt(saldo_reserva)}
                        - Metas Financeiras: {metas_str}
                        - Cenário atual: Selic em {selic_atual:.2f}% a.a., CDI em {cdi_atual:.2f}% a.a., IPCA em {ipca_atual:.2f}% a.a.

                        1. Avalie rapidamente se a relação reserva vs saldo livre está saudável.
                        2. Sugira uma alocação percentual prática para o Saldo Livre (ex: % em Liquidez, % em IPCA+, % em Prefixado/LCI/LCA ou FIIs).
                        3. Dê uma estratégia direta para atingir as metas mais rápido aproveitando os juros compostos.
                        Responda em Markdown bem estruturado.
                        """
                        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                        with st.container(border=True):
                            st.markdown("#### 🤖 Plano Recomendado pelo Consultor IA")
                            st.markdown(response.text)
                    except Exception as e:
                        st.error(f"Erro na comunicação com a IA: {e}. Verifique sua chave de API.")

    # ── Dica de reserva ───────────────────────────────────────────────
    if saldo_reserva > 0:
        rend_mensal_reserva = saldo_reserva * ((1 + cdi_atual / 100) ** (1 / 12) - 1)
        st.html(f"""
            <div class="insight-card" style="margin: 1rem 0 1.5rem 0; border-color: #4e8cff; background: rgba(78,140,255,0.05);">
                <span class="insight-icon">🛡️</span>
                <div>
                    <div class="insight-text" style="font-size: 0.9rem;">
                        Você tem <strong>{fmt(saldo_reserva)}</strong> na sua <strong>Reserva de Emergência</strong>!
                        A 100% do CDI ({cdi_atual:.2f}% a.a.), ela rende cerca de <strong>{fmt(rend_mensal_reserva)}/mês</strong> bruto.
                    </div>
                    <div class="insight-text" style="margin-top: 0.4rem;">
                        Mantenha-a em <strong>Tesouro Selic</strong> ou <strong>CDB 100% CDI de Liquidez Diária</strong> para segurança total e resgate imediato.
                    </div>
                </div>
            </div>
        """)
    else:
        st.html("""
            <div class="insight-card" style="margin: 1rem 0 1.5rem 0; border-color: #f59e0b; background: rgba(245,158,11,0.05);">
                <span class="insight-icon">⚠️</span>
                <div>
                    <div class="insight-text">Você ainda não declarou nenhum valor na sua <strong>Reserva de Emergência</strong>.</div>
                    <div class="insight-text" style="margin-top: 0.4rem;">Antes de buscar prazos longos, construa sua reserva (6x seus custos mensais) no <strong>Tesouro Selic</strong> ou <strong>CDB 100% CDI com Liquidez Diária</strong>.</div>
                </div>
            </div>
        """)

    # ── Simulador Side-by-Side ─────────────────────────────────────────────────────
    sec("⚖️", "Comparador de Investimentos (Lado a Lado)")
    st.caption("Simule com as taxas reais do mercado, personalize rentabilidades e veja o poder de compra descontando a inflação.")

    col_input1, col_input2, col_input3, col_input4 = st.columns([1.2, 1.2, 1, 1])
    with col_input1:
        capital = st.number_input("💰 Valor inicial (R$)", min_value=0.0, value=1000.0, step=100.0, format="%.2f", key="cap_sim")
    with col_input2:
        aporte = st.number_input("📥 Aporte mensal (R$)", min_value=0.0, value=500.0, step=50.0, format="%.2f", key="apo_sim")
    with col_input3:
        prazo = st.number_input("📅 Prazo (meses)", min_value=1, max_value=360, value=24, step=6, key="prz_sim")
    with col_input4:
        st.html("<div style='height:1.6rem;'></div>")
        descontar_ipca = st.checkbox(f"📉 Descontar IPCA ({ipca_atual:.1f}%)", value=False, help="Mostra o valor líquido ajustado pelo poder de compra (ganho real acima da inflação).")

    st.markdown("---")

    opcoes = {
        f"🏛️ Tesouro Selic ({selic_atual:.2f}% a.a.)": (selic_atual, False),
        f"🏦 CDB 100% CDI ({cdi_atual:.2f}% a.a.)": (cdi_atual, False),
        f"🏦 CDB 115% CDI ({cdi_atual * 1.15:.2f}% a.a.)": (round(cdi_atual * 1.15, 2), False),
        f"🏦 CDB 120% CDI ({cdi_atual * 1.20:.2f}% a.a.)": (round(cdi_atual * 1.20, 2), False),
        f"🏠 LCI/LCA 92% CDI Isento ({cdi_atual * 0.92:.2f}% a.a.)": (round(cdi_atual * 0.92, 2), True),
        f"🌾 CRI/CRA / Debênture Incentivada (IPCA + 7% = {ipca_atual + 7.0:.2f}% a.a.)": (round(ipca_atual + 7.0, 2), True),
        "💰 Poupança (~7,15% a.a. Isento)": (7.15, True),
        "⚙️ Taxa Personalizada": (None, False),
    }

    col_op1, col_op2 = st.columns(2)
    with col_op1:
        st.markdown("**Opção A**")
        opcao_a = st.selectbox("Escolha A", list(opcoes.keys()), index=0, key="op_a", label_visibility="collapsed")
        taxa_a_padrao, is_isento_a = opcoes[opcao_a]
        if taxa_a_padrao is None:
            ca_t, ca_i = st.columns([2, 1])
            with ca_t:
                taxa_a = st.number_input("Taxa Anual A (%)", min_value=0.1, max_value=50.0, value=15.0, step=0.25, key="tx_pers_a")
            with ca_i:
                is_isento_a = st.checkbox("Isento IR", key="isento_pers_a")
        else:
            taxa_a = taxa_a_padrao

    with col_op2:
        st.markdown("**Opção B**")
        opcao_b = st.selectbox("Escolha B", list(opcoes.keys()), index=4, key="op_b", label_visibility="collapsed")
        taxa_b_padrao, is_isento_b = opcoes[opcao_b]
        if taxa_b_padrao is None:
            cb_t, cb_i = st.columns([2, 1])
            with cb_t:
                taxa_b = st.number_input("Taxa Anual B (%)", min_value=0.1, max_value=50.0, value=12.0, step=0.25, key="tx_pers_b")
            with cb_i:
                is_isento_b = st.checkbox("Isento IR", key="isento_pers_b")
        else:
            taxa_b = taxa_b_padrao

    if (capital > 0 or aporte > 0) and prazo > 0:
        inflacao_param = ipca_atual if descontar_ipca else 0.0
        sim_a = simular_investimento(capital, aporte, prazo, taxa_a, inflacao_anual=inflacao_param, isento_ir=is_isento_a)
        sim_b = simular_investimento(capital, aporte, prazo, taxa_b, inflacao_anual=inflacao_param, isento_ir=is_isento_b)

        chave_final = "liquido_real" if descontar_ipca else "liquido"
        val_final_a = sim_a[chave_final]
        val_final_b = sim_b[chave_final]

        diff = val_final_a - val_final_b
        vencedor = f"Opção A ({opcao_a.split('(')[0].strip()})" if diff > 0 else (f"Opção B ({opcao_b.split('(')[0].strip()})" if diff < 0 else "Empate Técnico")

        st.html(f"""
            <div style="text-align:center; padding: 1rem; background: rgba(0,212,170,0.05); border: 1px solid rgba(0,212,170,0.2); border-radius: 12px; margin: 1rem 0;">
                <div style="font-size: 0.9rem; color: var(--text2);">🏆 Melhor retorno líquido: <b>{vencedor}</b></div>
                <div style="font-size: 1.25rem; font-weight: 800; color: #00d4aa; margin-top: 0.2rem;">Vantagem de +{fmt(abs(diff))} no período</div>
            </div>
        """)

        c_r1, c_r2 = st.columns(2)
        for col_dest, titulo_op, sim_obj, venceu in [
            (c_r1, opcao_a, sim_a, diff >= 0),
            (c_r2, opcao_b, sim_b, diff < 0),
        ]:
            with col_dest:
                valor_exibido = sim_obj[chave_final]
                sub_label = "Líquido Real (Descontado IPCA)" if descontar_ipca else "Patrimônio Líquido Final"
                st.html(f"""
                    <div class="glass-card" style="border-left: 4px solid {'#00d4aa' if venceu else '#4e8cff'};">
                        <div style="font-size: 0.85rem; font-weight: 700; color: #fff; margin-bottom: 0.6rem;">{titulo_op}</div>
                        <div style="display:flex; justify-content:space-between; margin-bottom:0.25rem;">
                            <span style="font-size:0.75rem; color:var(--text2);">Total Investido:</span>
                            <span style="font-size:0.75rem; font-weight:600;">{fmt(sim_obj['investido'])}</span>
                        </div>
                        <div style="display:flex; justify-content:space-between; margin-bottom:0.25rem;">
                            <span style="font-size:0.75rem; color:var(--text2);">Juros Brutos:</span>
                            <span style="font-size:0.75rem; font-weight:600; color:var(--green);">+ {fmt(sim_obj['rendimento'])}</span>
                        </div>
                        <div style="display:flex; justify-content:space-between; margin-bottom:0.5rem; padding-bottom:0.5rem; border-bottom: 1px solid rgba(255,255,255,0.05);">
                            <span style="font-size:0.75rem; color:var(--text2);">Imposto de Renda ({sim_obj['aliquota']:.1f}%):</span>
                            <span style="font-size:0.75rem; font-weight:600; color:var(--red);">- {fmt(sim_obj['ir'])}</span>
                        </div>
                        <div style="display:flex; justify-content:space-between; align-items:flex-end;">
                            <span style="font-size:0.72rem; text-transform:uppercase; color:var(--text3);">{sub_label}</span>
                            <span style="font-size:1.35rem; font-weight:900; color:#fff;">{fmt(valor_exibido)}</span>
                        </div>
                    </div>
                """)

        # ── Gráfico de evolução comparativo ───────────────────────────────────────────
        st.html("<br>")
        sec("📈", "Curva de Evolução Patrimonial")

        hist_a = sim_a["historico"]
        hist_b = sim_b["historico"]
        campo_hist = "saldo_real" if descontar_ipca else "saldo"

        fig_inv = go.Figure()
        fig_inv.add_trace(go.Scatter(
            x=[h["mes"] for h in hist_a], y=[h[campo_hist] for h in hist_a],
            name="Opção A", mode="lines", line=dict(color="#00d4aa", width=2.5),
            fill="tozeroy", fillcolor="rgba(0,212,170,0.08)",
        ))
        fig_inv.add_trace(go.Scatter(
            x=[h["mes"] for h in hist_b], y=[h[campo_hist] for h in hist_b],
            name="Opção B", mode="lines", line=dict(color="#4e8cff", width=2.5),
            fill="tozeroy", fillcolor="rgba(78,140,255,0.05)",
        ))
        fig_inv.add_trace(go.Scatter(
            x=[h["mes"] for h in hist_a], y=[h["investido"] for h in hist_a],
            name="Total Desembolsado", mode="lines", line=dict(color="#8b95a5", width=2, dash="dash"),
        ))

        fig_inv.update_layout(
            **PLOTLY_LAYOUT, height=350,
            xaxis=dict(title="Meses", showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.03)"),
            hovermode="x unified",
        )
        st.plotly_chart(fig_inv, key="inv_comp_chart", use_container_width=True)

    # ── Mapa e Guia Rápido ───────────────────────────────────────────────────
    st.html("<br>")
    with st.expander("🗺️ Mapa de Decisão & Guia Rápido de Renda Fixa", expanded=False):
        col_i1, col_i2, col_i3 = st.columns(3)
        with col_i1:
            st.html(f"""
                <div class="glass-card">
                    <div style="font-size:1.3rem;margin-bottom:0.4rem;">🏛️</div>
                    <div style="font-size:0.85rem;font-weight:700;color:#f0f2f5;">Tesouro Selic</div>
                    <div style="font-size:0.72rem;color:#8b95a5;margin-top:0.3rem;">
                        • Risco soberano (mais seguro do país)<br>
                        • Liquidez diária (D+1)<br>
                        • Rende ~{selic_atual:.2f}% a.a.<br>
                        • IR regressivo (22,5% a 15%)<br>
                        • <strong style="color:#00d4aa;">Ideal para Reserva de Emergência</strong>
                    </div>
                </div>
            """)
        with col_i2:
            st.html(f"""
                <div class="glass-card">
                    <div style="font-size:1.3rem;margin-bottom:0.4rem;">🏦</div>
                    <div style="font-size:0.85rem;font-weight:700;color:#f0f2f5;">CDB 100% a 120% CDI</div>
                    <div style="font-size:0.72rem;color:#8b95a5;margin-top:0.3rem;">
                        • Garantido pelo FGC (até R$ 250 mil)<br>
                        • Liquidez diária ou no vencimento<br>
                        • Rende ~{cdi_atual:.2f}% a {cdi_atual*1.2:.2f}% a.a.<br>
                        • IR regressivo<br>
                        • <strong style="color:#4e8cff;">Ótimo para metas de curto/médio prazo</strong>
                    </div>
                </div>
            """)
        with col_i3:
            st.html(f"""
                <div class="glass-card">
                    <div style="font-size:1.3rem;margin-bottom:0.4rem;">🏠</div>
                    <div style="font-size:0.85rem;font-weight:700;color:#f0f2f5;">LCI / LCA</div>
                    <div style="font-size:0.72rem;color:#8b95a5;margin-top:0.3rem;">
                        • <strong>Isento de Imposto de Renda</strong><br>
                        • Garantido pelo FGC<br>
                        • 90% CDI equivale a ~109% CDI de um CDB<br>
                        • Possui carência legal mínima<br>
                        • <strong style="color:#a855f7;">Excelente retorno líquido</strong>
                    </div>
                </div>
            """)
