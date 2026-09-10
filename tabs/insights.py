"""
tabs/insights.py — Aba de Insights e análise financeira.
Versão 2.0: Insights com prioridade, radar de saúde, heatmap melhorado, tooltips contextuais.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from core.utils import fmt, get_pref, MESES_PT, TAXA_SIMPLES, PLOTLY_LAYOUT
from core.database import read_sql
import html
from components.cards import sec, ring_progress
from components.tooltip_helper import get_tooltip
from intelligence.insights import gerar_insights


def render(ctx):
    """Renderiza a aba Insights."""
    conn = ctx["conn"]
    prefixo_mes = ctx["prefixo_mes"]
    mes_sel = ctx["mes_sel"]
    ano_sel = ctx["ano_sel"]
    rec_mes = ctx["rec_mes"]
    desp_mes = ctx["desp_mes"]
    simples_mes = ctx["simples_mes"]
    balanco_mes = ctx["balanco_mes"]
    saldo_total = ctx["saldo_total"]
    hoje = ctx["hoje"]
    dias_mes = ctx["dias_mes"]

    # ══════════════════════════════════════════════════════════════════
    # RADAR DE SAÚDE FINANCEIRA
    # ══════════════════════════════════════════════════════════════════
    sec("🎯", "Radar de Saúde Financeira")
    st.caption("Visão rápida de 5 pilares da sua vida financeira.")
    
    saldo_reserva = ctx.get("saldo_reserva", 0)
    score = ctx.get("score", 0)
    
    # Calcular scores por pilar
    # 1. Economia (% que sobra da receita)
    economia_score = max(0, min(100, ((rec_mes - desp_mes - simples_mes) / max(rec_mes, 1)) * 200))
    
    # 2. Investimento (se tem reserva/investimento)
    investimento_score = min(100, (saldo_reserva / max(desp_mes * 3, 1)) * 100) if desp_mes > 0 else 0
    
    # 3. Controle de gastos (% do orçamento usado)
    total_orc = conn.execute("SELECT COALESCE(SUM(valor_limite),0) FROM orcamentos WHERE mes=? AND ano=?", (mes_sel, ano_sel)).fetchone()[0]
    if total_orc > 0:
        gasto_pct = min(desp_mes / total_orc, 1.5) 
        orcamento_score = max(0, 100 - (gasto_pct - 0.5) * 200) if gasto_pct > 0.5 else 100
    else:
        orcamento_score = 50  # Não tem orçamento, nota neutra
    
    # 4. Emergência (meses de reserva)
    if desp_mes > 0 and saldo_reserva > 0:
        meses_reserva = saldo_reserva / desp_mes
        emergencia_score = min(100, (meses_reserva / 6) * 100)
    else:
        emergencia_score = 0
    
    # 5. Dívida (se cartão está controlado)
    total_cc = conn.execute("SELECT COALESCE(SUM(limite_cartao),0) FROM contas WHERE tipo='Cartão de Crédito'").fetchone()[0]
    total_cc_usado = conn.execute("""
        SELECT COALESCE(SUM(
            COALESCE((SELECT SUM(valor) FROM transacoes WHERE conta_id = c.id AND tipo='despesa'), 0) -
            COALESCE((SELECT SUM(valor) FROM transacoes WHERE conta_id = c.id AND tipo='receita'), 0)
        ), 0) FROM contas c WHERE c.tipo = 'Cartão de Crédito'
    """).fetchone()[0]
    if total_cc > 0:
        divida_score = max(0, 100 - (total_cc_usado / total_cc * 100))
    else:
        divida_score = 100  # Sem cartão = sem dívida

    fig_radar = go.Figure()
    
    categorias_radar = ['Economia', 'Investimento', 'Orçamento', 'Emergência', 'Dívida']
    valores = [economia_score, investimento_score, orcamento_score, emergencia_score, divida_score]
    
    # Área ideal (tudo 70+)
    fig_radar.add_trace(go.Scatterpolar(
        r=[70]*5 + [70],
        theta=categorias_radar + [categorias_radar[0]],
        fill='toself',
        fillcolor='rgba(0,212,170,0.05)',
        line=dict(color='rgba(0,212,170,0.3)', width=1, dash='dash'),
        name='Zona Ideal (70+)',
    ))
    
    fig_radar.add_trace(go.Scatterpolar(
        r=valores + [valores[0]],
        theta=categorias_radar + [categorias_radar[0]],
        fill='toself',
        fillcolor='rgba(78,140,255,0.15)',
        line=dict(color='#4e8cff', width=3),
        name='Sua Situação',
        hovertemplate='%{theta}: %{r:.0f}/100<extra></extra>',
    ))
    
    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], showticklabels=True, 
                          tickfont=dict(size=9, color='#5a6478'),
                          gridcolor='rgba(255,255,255,0.05)'),
            angularaxis=dict(tickfont=dict(size=11, color='#8b95a5'),
                           gridcolor='rgba(255,255,255,0.05)'),
            bgcolor='rgba(0,0,0,0)',
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter', color='#8b95a5'),
        height=320,
        margin=dict(l=60, r=60, t=30, b=30),
        legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(size=10)),
        showlegend=True,
    )
    st.plotly_chart(fig_radar, key="radar_health")

    # Mini-cards de cada pilar
    pilares = [
        ("💰", "Economia", economia_score, "#00d4aa"),
        ("📈", "Investimento", investimento_score, "#4e8cff"),
        ("📊", "Orçamento", orcamento_score, "#a855f7"),
        ("🛡️", "Emergência", emergencia_score, "#f59e0b"),
        ("💳", "Dívida", divida_score, "#06b6d4"),
    ]
    cols_p = st.columns(5)
    for i, (icon, nome, valor, cor) in enumerate(pilares):
        with cols_p[i]:
            ring_html = ring_progress(valor, size=45, stroke=4, color=cor, label=f"{valor:.0f}")
            st.markdown(f"""
                <div class="glass-card" style="text-align:center;padding:0.7rem;">
                    {ring_html}
                    <div style="font-size:0.68rem;color:var(--text2);margin-top:0.3rem;">{icon} {nome}</div>
                </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════
    # DICAS PERSONALIZADAS (com prioridade)
    # ══════════════════════════════════════════════════════════════════
    sec("💡", "Dicas Personalizadas")
    st.caption("Análise automática baseada nos seus dados reais.")

    insights = gerar_insights(conn, rec_mes, desp_mes, simples_mes, prefixo_mes, mes_sel, ano_sel, saldo_total)
    for idx, (icone, label, texto) in enumerate(insights):
        # Determinar prioridade baseada no ícone/conteúdo
        if any(w in texto.lower() for w in ["atenção", "cuidado", "ultrapass", "alto"]):
            priority_cls = "critical"
            priority_text = "ATENÇÃO"
        elif any(w in texto.lower() for w in ["dica", "sugest", "considere", "pode"]):
            priority_cls = "warning"
            priority_text = "DICA"
        else:
            priority_cls = "positive"
            priority_text = "POSITIVO"
        
        st.markdown(f"""
            <div class="insight-card" style="animation-delay:{idx * 0.08}s;">
                <span class="insight-icon">{icone}</span>
                <div>
                    <span class="insight-priority {priority_cls}">{priority_text}</span>
                    <div class="insight-text">{texto}</div>
                    <div class="insight-label">{label}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # ── IA Consultor de Custos ─────────────────────────────────────────
    with st.expander("🤖 Consultor de Redução de Custos (IA Gemini)", expanded=False):
        st.markdown("A Inteligência Artificial vai analisar todos os seus gastos deste mês e sugerir cortes precisos e planos de economia.")
        
        import google.genai as genai
        api_key_custos = st.text_input(
            "Chave de API do Google Gemini", type="password",
            key="gemini_key_custos",
            help="Pegue sua chave gratuitamente no Google AI Studio (aistudio.google.com).",
        )

        if st.button("Analisar Meus Gastos", type="primary"):
            if not api_key_custos:
                st.error("Por favor, insira sua Chave de API para usar a Inteligência Artificial.")
            else:
                with st.spinner("A IA está analisando suas transações. Isso pode levar alguns segundos..."):
                    try:
                        client = genai.Client(api_key=api_key_custos)
                        
                        txs_ia = conn.execute(
                            "SELECT t.descricao, t.valor, c.nome, t.data FROM transacoes t "
                            "LEFT JOIN categorias c ON t.categoria_id = c.id "
                            "WHERE t.tipo = 'despesa' AND t.data LIKE ?", (f"{prefixo_mes}%",)
                        ).fetchall()
                        
                        if not txs_ia:
                            st.warning("Você não tem gastos registrados neste mês para analisar.")
                        else:
                            gastos_str = "\\n".join([f"- {tx[3]}: {tx[0]} ({tx[2]}) -> R$ {tx[1]:.2f}" for tx in txs_ia])
                            
                            prompt = f"""
                            Atue como um consultor financeiro implacável especializado em redução de custos pessoais.
                            O usuário quer saber onde ele pode cortar gastos baseado nas transações deste mês.
                            
                            Resumo do mês:
                            Receitas: R$ {rec_mes:.2f}
                            Despesas: R$ {desp_mes:.2f}
                            
                            Lista detalhada de Despesas:
                            {gastos_str}
                            
                            Sua tarefa:
                            1. Identifique os 3 maiores gargalos ou gastos supérfluos (se houver).
                            2. Sugira cortes ou trocas práticas (ex: 'trocar plano A por B', 'reduzir ifood', etc).
                            3. Dê uma nota de 0 a 10 para o controle de gastos deste mês.
                            
                            Responda diretamente ao usuário com tom amigável mas firme. Formate a resposta usando Markdown (listas, negritos). Não crie textos muito longos, seja direto ao ponto.
                            """
                            
                            response = client.models.generate_content(
                                model='gemini-2.5-flash',
                                contents=prompt
                            )
                            
                            st.markdown("""
                            <div style="background:rgba(168,85,247,0.1); border-left:4px solid var(--purple); padding:1rem; border-radius:8px; margin-top:1rem;">
                                <h4 style="color:var(--purple); margin-top:0;">🤖 Análise da I.A. Concluída</h4>
                            """, unsafe_allow_html=True)
                            
                            st.markdown(response.text)
                            
                            st.markdown("</div>", unsafe_allow_html=True)
                            
                    except Exception as e:
                        st.error(f"Erro ao consultar a IA: {e}")

    st.markdown("<br>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════
    # COMPARATIVO COM MÊS ANTERIOR (melhorado)
    # ══════════════════════════════════════════════════════════════════
    sec("📊", "Comparativo com Mês Anterior")
    p_ant, m_ant, a_ant = get_pref(mes_sel - 1, ano_sel)
    rec_ant = conn.execute(
        "SELECT COALESCE(SUM(valor),0) FROM transacoes WHERE tipo='receita' AND COALESCE(is_transferencia,0)=0 AND data LIKE ?",
        (f"{p_ant}%",),
    ).fetchone()[0]
    desp_ant = conn.execute(
        "SELECT COALESCE(SUM(valor),0) FROM transacoes WHERE tipo='despesa' AND COALESCE(is_transferencia,0)=0 AND data LIKE ?",
        (f"{p_ant}%",),
    ).fetchone()[0]

    col_c1, col_c2, col_c3 = st.columns(3)

    def comp_card(label, atual, anterior, icon, is_expense=False):
        if anterior > 0:
            var = ((atual - anterior) / anterior) * 100
            seta = "↑" if var > 0 else "↓"
            if is_expense:
                cor_var = "#ff4b6e" if var > 0 else "#00d4aa"
            else:
                cor_var = "#00d4aa" if var > 0 else "#ff4b6e"
        else:
            var, seta, cor_var = 0, "–", "#8b95a5"

        st.markdown(f"""
            <div class="glass-card" style="text-align: center;">
                <div style="font-size: 1.3rem; margin-bottom: 0.3rem;">{icon}</div>
                <div style="font-size: 0.7rem; color: var(--text2); text-transform: uppercase;">{label}</div>
                <div style="font-size: 1.2rem; font-weight: 700; color: var(--text);">{fmt(atual)}</div>
                <div style="font-size: 0.75rem; color: {cor_var}; font-weight: 600; margin-top: 0.2rem;">
                    {seta} {abs(var):.1f}% vs {MESES_PT[m_ant][:3]}
                </div>
                <div style="font-size: 0.68rem; color: var(--text3);">Anterior: {fmt(anterior)}</div>
            </div>
        """, unsafe_allow_html=True)

    with col_c1:
        comp_card("Receitas", rec_mes, rec_ant, "📈")
    with col_c2:
        comp_card("Despesas", desp_mes, desp_ant, "📉", is_expense=True)
    with col_c3:
        comp_card("Balanço", balanco_mes, rec_ant - desp_ant - rec_ant * TAXA_SIMPLES, "💰")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Previsão de gastos ────────────────────────────────────────────
    sec("🔮", "Previsão para o Restante do Mês")
    dia_atual = hoje.day if (hoje.month == mes_sel and hoje.year == ano_sel) else dias_mes
    if dia_atual > 0 and desp_mes > 0:
        media_diaria = desp_mes / dia_atual
        dias_restantes = dias_mes - dia_atual
        previsao = desp_mes + (media_diaria * dias_restantes)
        st.markdown(f"""
            <div class="glass-card">
                <div style="display: flex; justify-content: space-around; text-align: center;">
                    <div>
                        <div style="font-size: 0.7rem; color: var(--text2); text-transform: uppercase;">Média Diária</div>
                        <div style="font-size: 1.1rem; font-weight: 700; color: #f59e0b;">{fmt(media_diaria)}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.7rem; color: var(--text2); text-transform: uppercase;">Dias Restantes</div>
                        <div style="font-size: 1.1rem; font-weight: 700; color: #4e8cff;">{dias_restantes}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.7rem; color: var(--text2); text-transform: uppercase;">Previsão Total</div>
                        <div style="font-size: 1.1rem; font-weight: 700; color: #ff4b6e;">{fmt(previsao)}</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.info("Sem dados suficientes para previsão.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Média últimos 3 meses por categoria ───────────────────────────
    sec("📋", "Média de Gastos (3 meses) por Categoria")
    media_cats = read_sql("""
        SELECT c.icone, c.nome, AVG(sub.total) as media FROM (
            SELECT t.categoria_id, SUM(t.valor) as total, substr(t.data,1,7) as mes
            FROM transacoes t WHERE t.tipo='despesa'
            GROUP BY t.categoria_id, substr(t.data,1,7)
        ) sub JOIN categorias c ON sub.categoria_id = c.id
        GROUP BY c.id ORDER BY media DESC LIMIT 8
    """, conn)
    if not media_cats.empty:
        cols_mc = st.columns(4)
        for i, (_, row) in enumerate(media_cats.iterrows()):
            with cols_mc[i % 4]:
                st.markdown(f"""
                    <div class="glass-card" style="text-align: center; padding: 0.8rem;">
                        <div style="font-size: 1.3rem;">{row['icone']}</div>
                        <div style="font-size: 0.75rem; color: var(--text2); margin: 0.2rem 0;">{row['nome']}</div>
                        <div style="font-size: 0.95rem; font-weight: 700; color: var(--text);">{fmt(row['media'])}/mês</div>
                    </div>
                """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # ── Evolução de Categorias (6 meses) ───────────────────────────
    sec("📈", "Evolução de Categorias (Últimos 6 meses)")
    
    mes_ant6 = mes_sel - 5
    ano_ant6 = ano_sel
    if mes_ant6 <= 0:
        mes_ant6 += 12
        ano_ant6 -= 1
    p_ant6 = f"{ano_ant6}-{mes_ant6:02d}"
    
    cat_evol_df = read_sql("""
        SELECT c.nome, substr(t.data,1,7) as mes, SUM(t.valor) as total
        FROM transacoes t
        JOIN categorias c ON t.categoria_id = c.id
        WHERE t.tipo = 'despesa' AND substr(t.data,1,7) >= ?
        GROUP BY c.nome, substr(t.data,1,7)
    """, conn, params=(p_ant6,))
    
    if not cat_evol_df.empty:
        cats_disponiveis = cat_evol_df["nome"].unique().tolist()
        cats_selecionadas = st.multiselect("Selecione as categorias para comparar:", cats_disponiveis, default=cats_disponiveis[:3] if len(cats_disponiveis)>=3 else cats_disponiveis)
        
        if cats_selecionadas:
            fig_cat = go.Figure()
            for cat in cats_selecionadas:
                df_cat = cat_evol_df[cat_evol_df["nome"] == cat].sort_values("mes")
                fig_cat.add_trace(go.Scatter(x=df_cat["mes"], y=df_cat["total"], mode="lines+markers", name=cat, line=dict(width=3)))
                
            fig_cat.update_layout(**PLOTLY_LAYOUT, height=300, yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.03)"), xaxis=dict(showgrid=False))
            st.plotly_chart(fig_cat, width='stretch')
    else:
        st.info("Sem dados suficientes para os últimos 6 meses.")
    st.markdown("<br>", unsafe_allow_html=True)

    # ── Heatmap: Gastos por Dia da Semana ──────────────────────────────
    sec("📅", "Gastos por Dia da Semana")
    dias_semana_map = {0: "Seg", 1: "Ter", 2: "Qua", 3: "Qui", 4: "Sex", 5: "Sáb", 6: "Dom"}
    txs_mes = read_sql(
        "SELECT data, valor FROM transacoes WHERE tipo='despesa' AND data LIKE ?",
        conn, params=(f"{prefixo_mes}%",),
    )
    if not txs_mes.empty:
        txs_mes["dia_semana"] = pd.to_datetime(txs_mes["data"]).dt.dayofweek
        gastos_dia = txs_mes.groupby("dia_semana")["valor"].sum().reindex(range(7), fill_value=0)
        
        max_val = gastos_dia.max() if gastos_dia.max() > 0 else 1
        
        cols_hm = st.columns(7)
        for d in range(7):
            val = gastos_dia[d]
            intensidade = min(val / max_val, 1.0)
            # Gradiente do azul ao vermelho
            r = int(30 + intensidade * 225)
            g = int(40 + (1 - intensidade) * 100)
            b = int(100 - intensidade * 50)
            cor_bg = f"rgba({r},{g},{b},{0.15 + intensidade * 0.4})"
            
            with cols_hm[d]:
                st.markdown(f"""
                    <div style="background:{cor_bg}; border-radius:10px; padding:0.8rem 0.2rem; text-align:center; display:flex; flex-direction:column; justify-content:center; min-height:80px; border:1px solid rgba(255,255,255,0.05); transition:all 0.3s;">
                        <div style="font-size:0.75rem; font-weight:700; color:var(--text);">{dias_semana_map[d]}</div>
                        <div style="font-size:0.8rem; font-weight:800; color:#fff; margin-top:0.3rem;">{fmt(val)}</div>
                    </div>
                """, unsafe_allow_html=True)
                
        dia_max = gastos_dia.idxmax()
        val_max = gastos_dia.max()
        if val_max > 0:
            st.markdown(f"""
                <div class="alert-card warning" style="margin-top:1rem;">
                    <span class="alert-icon">💡</span>
                    <span class="alert-text"><b>Insight Automático:</b> Você costuma gastar mais às <b>{dias_semana_map[dia_max]}s-feiras</b> (média de {fmt(val_max)}).</span>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Sem dados suficientes para o mapa de calor de gastos neste mês.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Heatmap Estilo GitHub (Atividade) ──────────────────────────────
    sec("🔥", "Frequência de Registros (Últimos 6 meses)")
    st.caption("Acompanhe sua consistência em registrar transações (Gamificação).")
    
    import datetime
    seis_meses_atras = hoje - datetime.timedelta(days=180)
    txs_freq = read_sql(
        "SELECT data, COUNT(id) as qtd FROM transacoes WHERE data >= ? GROUP BY data",
        conn, params=(seis_meses_atras.strftime("%Y-%m-%d"),)
    )
    
    # Criar um dict de data -> qtd
    dict_freq = {}
    if not txs_freq.empty:
        dict_freq = {r["data"]: r["qtd"] for _, r in txs_freq.iterrows()}
        
    max_qtd = max(dict_freq.values()) if dict_freq else 1
    
    # Gerar a matriz de 7 dias x ~26 semanas
    dias_grid = []
    curr_date = seis_meses_atras
    
    # Preencher espaços vazios até segunda-feira
    offset_inicio = curr_date.weekday()
    semana_atual = [None] * offset_inicio
    
    while curr_date <= hoje:
        semana_atual.append(curr_date)
        if len(semana_atual) == 7:
            dias_grid.append(semana_atual)
            semana_atual = []
        curr_date += datetime.timedelta(days=1)
        
    if semana_atual:
        while len(semana_atual) < 7:
            semana_atual.append(None)
        dias_grid.append(semana_atual)
        
    # Renderizar HTML do grid
    gh_html = '<div style="display:flex; gap:4px; overflow-x:auto; padding-bottom:10px;">'
    
    for semana in dias_grid:
        gh_html += '<div style="display:flex; flex-direction:column; gap:4px;">'
        for dia_data in semana:
            if dia_data is None:
                gh_html += '<div style="width:12px; height:12px; border-radius:3px; background:transparent;"></div>'
            else:
                str_d = dia_data.strftime("%Y-%m-%d")
                qtd = dict_freq.get(str_d, 0)
                
                if qtd == 0:
                    cor_bg = "rgba(255,255,255,0.05)"
                else:
                    # Cores estilo GitHub (tons de verde/azul)
                    intensidade = min(qtd / max_qtd, 1.0)
                    r = int(11 + (0 - 11) * intensidade)
                    g = int(255 * intensidade)
                    b = int(110 + (170 - 110) * intensidade)
                    cor_bg = f"rgba(0, 212, 170, {max(0.3, intensidade)})"
                    
                tooltip_txt = f"{qtd} transações em {str_d}" if qtd > 0 else f"Sem registros em {str_d}"
                gh_html += f'<div title="{tooltip_txt}" style="width:12px; height:12px; border-radius:3px; background:{cor_bg}; border: 1px solid rgba(255,255,255,0.02);"></div>'
        gh_html += '</div>'
    gh_html += '</div>'
    
    # Legenda
    gh_html += """
    <div style="display:flex; align-items:center; gap:5px; font-size:0.65rem; color:var(--text3); margin-top:0.5rem; justify-content:flex-end;">
        <span>Menos</span>
        <div style="width:12px; height:12px; border-radius:3px; background:rgba(255,255,255,0.05);"></div>
        <div style="width:12px; height:12px; border-radius:3px; background:rgba(0,212,170,0.3);"></div>
        <div style="width:12px; height:12px; border-radius:3px; background:rgba(0,212,170,0.6);"></div>
        <div style="width:12px; height:12px; border-radius:3px; background:rgba(0,212,170,1.0);"></div>
        <span>Mais</span>
    </div>
    """
    
    st.markdown(f"""
        <div class="glass-card" style="padding: 1rem;">
            {gh_html}
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Projeção de Patrimônio - 12 Meses ──────────────────────────
    sec("🔮", "Projeção de Patrimônio (12 meses)")
    st.caption("Baseado na sua média de economia dos últimos 3 meses.")
    
    sobras_3m = []
    for i in range(1, 4):
        p_ant_proj, m_ant_proj, a_ant_proj = get_pref(mes_sel - i, ano_sel)
        r_ant = conn.execute("SELECT COALESCE(SUM(valor),0) FROM transacoes WHERE tipo='receita' AND COALESCE(is_transferencia,0)=0 AND data LIKE ?", (f"{p_ant_proj}%",)).fetchone()[0]
        d_ant = conn.execute("SELECT COALESCE(SUM(valor),0) FROM transacoes WHERE tipo='despesa' AND COALESCE(is_transferencia,0)=0 AND data LIKE ?", (f"{p_ant_proj}%",)).fetchone()[0]
        s_ant = r_ant * TAXA_SIMPLES
        sobras_3m.append(max(0, r_ant - d_ant - s_ant))
    
    media_sobra = sum(sobras_3m) / len(sobras_3m) if sobras_3m else 0
    
    if media_sobra > 0:
        meses_proj = []
        proj_real = []
        proj_otimista = []
        proj_pessimista = []
        
        patrimonio_base = saldo_total + ctx.get("saldo_reserva", 0)
        acumulado = patrimonio_base
        acumulado_ot = patrimonio_base
        acumulado_pe = patrimonio_base
        
        taxa = 0.01
        
        for i in range(1, 13):
            p_futuro, m_futuro, a_futuro = get_pref(mes_sel + i, ano_sel)
            meses_proj.append(f"{MESES_PT[m_futuro][:3]}/{str(a_futuro)[2:]}")
            
            acumulado = (acumulado * (1 + taxa)) + media_sobra
            proj_real.append(acumulado)
            
            acumulado_ot = (acumulado_ot * (1 + taxa)) + (media_sobra * 1.2)
            proj_otimista.append(acumulado_ot)
            
            acumulado_pe = (acumulado_pe * (1 + taxa)) + (media_sobra * 0.8)
            proj_pessimista.append(acumulado_pe)

        fig_proj = go.Figure()
        
        fig_proj.add_trace(go.Scatter(
            x=meses_proj + meses_proj[::-1],
            y=proj_otimista + proj_pessimista[::-1],
            fill='toself',
            fillcolor='rgba(78, 140, 255, 0.08)',
            line=dict(color='rgba(255,255,255,0)'),
            hoverinfo="skip",
            showlegend=False
        ))
        
        fig_proj.add_trace(go.Scatter(
            x=meses_proj, y=proj_real,
            mode='lines+markers',
            name='Cenário Base',
            line=dict(color='#4e8cff', width=3),
            marker=dict(size=6, color='#4e8cff'),
            hovertemplate='%{x}<br>Patrimônio: R$ %{y:,.2f}<extra></extra>'
        ))
        
        fig_proj.add_trace(go.Scatter(
            x=meses_proj, y=proj_otimista,
            mode='lines',
            name='Otimista (+20% eco.)',
            line=dict(color='#00d4aa', width=1.5, dash='dash'),
            hovertemplate='%{x}<br>Otimista: R$ %{y:,.2f}<extra></extra>'
        ))
        
        fig_proj.add_trace(go.Scatter(
            x=meses_proj, y=proj_pessimista,
            mode='lines',
            name='Pessimista (-20% eco.)',
            line=dict(color='#ff4b6e', width=1.5, dash='dash'),
            hovertemplate='%{x}<br>Pessimista: R$ %{y:,.2f}<extra></extra>'
        ))

        proj_layout = {**PLOTLY_LAYOUT, "legend": dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(0,0,0,0)", font=dict(color="#8b95a5", size=11))}
        fig_proj.update_layout(
            **proj_layout, height=320,
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.03)"),
            hovermode="x unified",
        )
        st.plotly_chart(fig_proj, key="proj_chart")
        
        st.markdown(f"""
            <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.05); padding:1rem; border-radius:12px; margin-top:0.5rem;">
                <div>
                    <div style="font-size:0.7rem; color:var(--text2); text-transform:uppercase;">Economia Média Mensal (Últ. 3 meses)</div>
                    <div style="font-size:1.2rem; font-weight:800; color:var(--text);">{fmt(media_sobra)}</div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:0.7rem; color:var(--text2); text-transform:uppercase;">Projeção de Patrimônio em 1 Ano</div>
                    <div style="font-size:1.4rem; font-weight:900; color:#4e8cff;">{fmt(proj_real[-1])}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.info("Para gerar uma projeção, você precisa ter uma média de economia (sobra positiva) nos últimos 3 meses.")
