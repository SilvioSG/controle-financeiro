"""
tabs/insights.py — Aba de Insights e análise financeira.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from core.utils import fmt, get_pref, MESES_PT, TAXA_SIMPLES, PLOTLY_LAYOUT
from core.database import read_sql
import html
from components.cards import sec
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

    # ── Dicas Personalizadas ──────────────────────────────────────────
    sec("💡", "Dicas Personalizadas")
    st.caption("Análise automática baseada nos seus dados reais.")

    insights = gerar_insights(conn, rec_mes, desp_mes, simples_mes, prefixo_mes, mes_sel, ano_sel, saldo_total)
    for icone, label, texto in insights:
        st.markdown(f"""
            <div class="insight-card">
                <span class="insight-icon">{icone}</span>
                <div>
                    <div class="insight-text">{texto}</div>
                    <div class="insight-label">{label}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Comparativo mês atual vs anterior ─────────────────────────────
    sec("📊", "Comparativo com Mês Anterior")
    p_ant, m_ant, a_ant = get_pref(mes_sel - 1, ano_sel)
    rec_ant = conn.execute(
        "SELECT COALESCE(SUM(valor),0) FROM transacoes WHERE tipo='receita' AND data LIKE ?",
        (f"{p_ant}%",),
    ).fetchone()[0]
    desp_ant = conn.execute(
        "SELECT COALESCE(SUM(valor),0) FROM transacoes WHERE tipo='despesa' AND data LIKE ?",
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
                <div style="font-size: 0.7rem; color: #8b95a5; text-transform: uppercase;">{label}</div>
                <div style="font-size: 1.2rem; font-weight: 700; color: #f0f2f5;">{fmt(atual)}</div>
                <div style="font-size: 0.75rem; color: {cor_var}; font-weight: 600; margin-top: 0.2rem;">
                    {seta} {abs(var):.1f}% vs {MESES_PT[m_ant][:3]}
                </div>
                <div style="font-size: 0.68rem; color: #5a6478;">Anterior: {fmt(anterior)}</div>
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
                        <div style="font-size: 0.7rem; color: #8b95a5; text-transform: uppercase;">Média Diária</div>
                        <div style="font-size: 1.1rem; font-weight: 700; color: #f59e0b;">{fmt(media_diaria)}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.7rem; color: #8b95a5; text-transform: uppercase;">Dias Restantes</div>
                        <div style="font-size: 1.1rem; font-weight: 700; color: #4e8cff;">{dias_restantes}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.7rem; color: #8b95a5; text-transform: uppercase;">Previsão Total</div>
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
                        <div style="font-size: 0.75rem; color: #8b95a5; margin: 0.2rem 0;">{row['nome']}</div>
                        <div style="font-size: 0.95rem; font-weight: 700; color: #f0f2f5;">{fmt(row['media'])}/mês</div>
                    </div>
                """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # ── Evolução de Categorias (6 meses) (Fase 3.4) ───────────────────
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

    # ── Heatmap: Gastos por Dia da Semana (Fase 3.3) ──────────────────
    sec("📅", "Gastos por Dia da Semana")
    dias_semana_map = {0: "Seg", 1: "Ter", 2: "Qua", 3: "Qui", 4: "Sex", 5: "Sáb", 6: "Dom"}
    txs_mes = read_sql(
        "SELECT data, valor FROM transacoes WHERE tipo='despesa' AND data LIKE ?",
        conn, params=(f"{prefixo_mes}%",),
    )
    if not txs_mes.empty:
        txs_mes["dia_semana"] = pd.to_datetime(txs_mes["data"]).dt.dayofweek
        gastos_dia = txs_mes.groupby("dia_semana")["valor"].sum().reindex(range(7), fill_value=0)
        
        # Cores quentes para heatmap (do azul pro vermelho)
        colors = ["rgba(78,140,255,0.2)", "rgba(78,140,255,0.5)", "rgba(0,212,170,0.5)", 
                  "rgba(0,212,170,0.8)", "rgba(245,158,11,0.6)", "rgba(245,158,11,0.9)", 
                  "rgba(255,75,110,0.9)"]
        
        max_val = gastos_dia.max() if gastos_dia.max() > 0 else 1
        
        cols_hm = st.columns(7)
        for d in range(7):
            val = gastos_dia[d]
            intensidade = min(int((val / max_val) * 6), 6)
            cor_bg = colors[intensidade]
            with cols_hm[d]:
                st.markdown(f"""
                    <div style="background:{cor_bg}; border-radius:10px; padding:0.8rem 0.2rem; text-align:center; display:flex; flex-direction:column; justify-content:center; min-height:80px; border:1px solid rgba(255,255,255,0.05);">
                        <div style="font-size:0.75rem; font-weight:700; color:#f0f2f5;">{dias_semana_map[d]}</div>
                        <div style="font-size:0.8rem; font-weight:800; color:#fff; margin-top:0.3rem;">{fmt(val)}</div>
                    </div>
                """, unsafe_allow_html=True)
                
        dia_max = gastos_dia.idxmax()
        val_max = gastos_dia.max()
        if val_max > 0:
            st.markdown(f"""
                <div style="margin-top: 1rem; padding: 0.8rem; background: rgba(245,158,11,0.1); border-left: 3px solid #f59e0b; border-radius: 4px;">
                    💡 <b>Insight Automático:</b> Você costuma gastar mais às <b>{dias_semana_map[dia_max]}s-feiras</b> (média de {fmt(val_max)}).
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Sem dados suficientes para o mapa de calor de gastos neste mês.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Projeção de Patrimônio - 12 Meses (Fase 4.4) ──────────────────
    sec("🔮", "Projeção de Patrimônio (12 meses)")
    st.caption("Baseado na sua média de economia dos últimos 3 meses.")
    
    # Calcular média de sobra dos últimos 3 meses
    sobras_3m = []
    for i in range(1, 4):
        p_ant, m_ant, a_ant = get_pref(mes_sel - i, ano_sel)
        r_ant = conn.execute("SELECT COALESCE(SUM(valor),0) FROM transacoes WHERE tipo='receita' AND data LIKE ?", (f"{p_ant}%",)).fetchone()[0]
        d_ant = conn.execute("SELECT COALESCE(SUM(valor),0) FROM transacoes WHERE tipo='despesa' AND data LIKE ?", (f"{p_ant}%",)).fetchone()[0]
        s_ant = r_ant * TAXA_SIMPLES
        sobras_3m.append(max(0, r_ant - d_ant - s_ant))
    
    media_sobra = sum(sobras_3m) / len(sobras_3m) if sobras_3m else 0
    
    if media_sobra > 0:
        meses_proj = []
        proj_real = []
        proj_otimista = []
        proj_pessimista = []
        
        acumulado = saldo_total
        acumulado_ot = saldo_total
        acumulado_pe = saldo_total
        
        # Taxa Selic aprox 1% a.m para a projeção
        taxa = 0.01
        
        for i in range(1, 13):
            # Mês projetado
            p_futuro, m_futuro, a_futuro = get_pref(mes_sel + i, ano_sel)
            meses_proj.append(f"{MESES_PT[m_futuro][:3]}/{str(a_futuro)[2:]}")
            
            # Realista (Média)
            acumulado = (acumulado * (1 + taxa)) + media_sobra
            proj_real.append(acumulado)
            
            # Otimista (+20% de economia)
            acumulado_ot = (acumulado_ot * (1 + taxa)) + (media_sobra * 1.2)
            proj_otimista.append(acumulado_ot)
            
            # Pessimista (-20% de economia)
            acumulado_pe = (acumulado_pe * (1 + taxa)) + (media_sobra * 0.8)
            proj_pessimista.append(acumulado_pe)

        fig_proj = go.Figure()
        
        # Área entre otimista e pessimista
        fig_proj.add_trace(go.Scatter(
            x=meses_proj + meses_proj[::-1],
            y=proj_otimista + proj_pessimista[::-1],
            fill='toself',
            fillcolor='rgba(78, 140, 255, 0.1)',
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

        fig_proj.update_layout(
            **PLOTLY_LAYOUT, height=320,
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.03)"),
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_proj, key="proj_chart")
        
        st.markdown(f"""
            <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.05); padding:1rem; border-radius:12px; margin-top:0.5rem;">
                <div>
                    <div style="font-size:0.7rem; color:#8b95a5; text-transform:uppercase;">Economia Média Mensal (Últ. 3 meses)</div>
                    <div style="font-size:1.2rem; font-weight:800; color:#f0f2f5;">{fmt(media_sobra)}</div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:0.7rem; color:#8b95a5; text-transform:uppercase;">Projeção de Patrimônio em 1 Ano</div>
                    <div style="font-size:1.4rem; font-weight:900; color:#4e8cff;">{fmt(proj_real[-1])}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.info("Para gerar uma projeção, você precisa ter uma média de economia (sobra positiva) nos últimos 3 meses.")
