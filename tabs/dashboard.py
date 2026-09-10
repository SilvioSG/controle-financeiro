"""
tabs/dashboard.py — Aba principal do Dashboard.
Versão 2.0: Hero card, KPIs com trend, calendário heatmap, feed de atividade, alertas premium.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import html
import calendar

from core.utils import fmt, get_pref, MESES_PT, PLOTLY_LAYOUT
from core.database import read_sql, saldo_conta
from components.cards import (
    metric_card, sec, hero_card, alert_card,
    activity_item, badge_card, ring_progress,
    calendar_day_cell,
)
from components.tooltip_helper import get_tooltip, render_tooltip_inline
from intelligence.score import calcular_score
from intelligence.rules import calcular_50_30_20


def render(ctx):
    """Renderiza a aba Dashboard."""
    conn = ctx["conn"]
    prefixo_mes = ctx["prefixo_mes"]
    mes_sel = ctx["mes_sel"]
    ano_sel = ctx["ano_sel"]
    rec_mes = ctx["rec_mes"]
    desp_mes = ctx["desp_mes"]
    simples_mes = ctx["simples_mes"]
    balanco_mes = ctx["balanco_mes"]
    saldo_total = ctx["saldo_total"]
    score = ctx["score"]
    score_cor = ctx["score_cor"]
    score_label = ctx["score_label"]
    dias_mes = ctx["dias_mes"]
    hoje = ctx["hoje"]
    saldo_reserva = ctx.get("saldo_reserva", 0)

    # ══════════════════════════════════════════════════════════════════
    # HERO CARD — Patrimônio Líquido
    # ══════════════════════════════════════════════════════════════════
    # Calcular patrimônio total (todas as contas)
    patrimonio = conn.execute("""
        SELECT COALESCE(SUM(
            COALESCE(c.saldo_inicial, 0) +
            COALESCE((SELECT SUM(valor) FROM transacoes WHERE conta_id = c.id AND tipo='receita'), 0) -
            COALESCE((SELECT SUM(valor) FROM transacoes WHERE conta_id = c.id AND tipo='despesa'), 0)
        ), 0) FROM contas c
    """).fetchone()[0]
    
    # Patrimônio do mês anterior para calcular variação
    p_ant, m_ant, a_ant = get_pref(mes_sel - 1, ano_sel)
    rec_ant = conn.execute(
        "SELECT COALESCE(SUM(valor),0) FROM transacoes WHERE tipo='receita' AND COALESCE(is_transferencia,0)=0 AND data LIKE ?",
        (f"{p_ant}%",),
    ).fetchone()[0]
    desp_ant = conn.execute(
        "SELECT COALESCE(SUM(valor),0) FROM transacoes WHERE tipo='despesa' AND COALESCE(is_transferencia,0)=0 AND data LIKE ?",
        (f"{p_ant}%",),
    ).fetchone()[0]
    
    balanco_ant = rec_ant - desp_ant - (rec_ant * 0.06)
    var_pct = ((balanco_mes - balanco_ant) / abs(balanco_ant) * 100) if balanco_ant != 0 else 0

    # Montar sparkline dos últimos 6 meses
    spark_data = []
    for i in range(5, -1, -1):
        p, m2, a2 = get_pref(mes_sel - i, ano_sel)
        r = conn.execute("SELECT COALESCE(SUM(valor),0) FROM transacoes WHERE tipo='receita' AND COALESCE(is_transferencia,0)=0 AND data LIKE ?", (f"{p}%",)).fetchone()[0]
        d = conn.execute("SELECT COALESCE(SUM(valor),0) FROM transacoes WHERE tipo='despesa' AND COALESCE(is_transferencia,0)=0 AND data LIKE ?", (f"{p}%",)).fetchone()[0]
        spark_data.append(r - d - (r * 0.06))

    # SVG Sparkline embutida (base64 para compatibilidade com st.markdown)
    if any(v != 0 for v in spark_data):
        max_s = max(abs(v) for v in spark_data) or 1
        min_s = min(spark_data)
        range_s = max(max_s - min_s, 1)
        points = []
        for i, v in enumerate(spark_data):
            x = i * (180 / max(len(spark_data) - 1, 1))
            y = 35 - ((v - min_s) / range_s) * 30
            points.append(f"{x},{y}")
        pts_str = " ".join(points)
        import base64
        svg_raw = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="190" height="40" viewBox="0 0 190 40">'
            f'<defs><linearGradient id="sg1" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0%" stop-color="rgba(0,212,170,0.3)"/>'
            f'<stop offset="100%" stop-color="rgba(0,212,170,0)"/>'
            f'</linearGradient></defs>'
            f'<polygon points="0,40 {pts_str} 180,40" fill="url(#sg1)"/>'
            f'<polyline points="{pts_str}" fill="none" stroke="#00d4aa" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
            f'</svg>'
        )
        b64 = base64.b64encode(svg_raw.encode()).decode()
        sparkline_svg = f'<img src="data:image/svg+xml;base64,{b64}" width="190" height="40" style="margin-top:0.5rem;">'
    else:
        sparkline_svg = ""

    change_cls = "positive" if var_pct >= 0 else "negative"
    change_arrow = "↑" if var_pct >= 0 else "↓"

    # Montar sub_parts
    sub_parts = []
    if saldo_reserva > 0:
        sub_parts.append(f"🛡️ Reserva: {fmt(saldo_reserva)}")
    sub_parts.append(f"💰 Balanço do mês: {fmt(balanco_mes)}")

    st.markdown(f"""
    <div class="hero-card">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:1rem;">
            <div style="flex:1;min-width:220px;">
                <div class="hero-label">
                    {render_tooltip_inline('💎 Patrimônio Líquido', 'patrimonio')}
                    <span style="margin-left:auto;font-size:0.6rem;color:var(--text3);display:flex;align-items:center;gap:0.3rem;">
                        <span class="live-dot"></span> Atualizado
                    </span>
                </div>
                <div class="hero-value">{fmt(patrimonio)}</div>
                <div class="hero-change {change_cls}">{change_arrow} {abs(var_pct):.1f}% vs {MESES_PT[m_ant][:3]}</div>
                <div class="hero-sub">{' · '.join(sub_parts)}</div>
            </div>
            <div style="flex-shrink:0;opacity:0.9;">
                {sparkline_svg}
                <div style="font-size:0.58rem;color:var(--text3);text-align:right;">Últimos 6 meses</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════
    # ALERTAS INTELIGENTES (Premium)
    # ══════════════════════════════════════════════════════════════════
    alertas = []
    
    if rec_mes > 0 and (desp_mes / rec_mes) > 0.8:
        alertas.append(("🚨", "Atenção: Suas despesas já ultrapassaram 80% da receita deste mês!", "critical"))
        
    if balanco_mes > 500:
        alertas.append(("💡", f"Você tem {fmt(balanco_mes)} sobrando este mês. Que tal guardar na Reserva?", "positive"))
        
    if hoje.month == mes_sel and hoje.year == ano_sel:
        recorrentes_count = conn.execute(
            "SELECT COUNT(id) FROM transacoes WHERE recorrente=1 AND tipo='despesa' AND data LIKE ? AND substr(data,9,2) > ?",
            (f"{prefixo_mes}%", f"{hoje.day:02d}")
        ).fetchone()[0]
        if recorrentes_count > 0:
            alertas.append(("⏰", f"Você tem {recorrentes_count} transações recorrentes previstas para os próximos dias.", "warning"))

    if alertas:
        alerts_html = "".join([alert_card(ic, msg, lvl) for ic, msg, lvl in alertas])
        st.markdown(alerts_html, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════
    # QUANTO POSSO GASTAR HOJE (Premium)
    # ══════════════════════════════════════════════════════════════════
    if rec_mes > 0 and hoje.month == mes_sel and hoje.year == ano_sel:
        dias_restantes = max(dias_mes - hoje.day, 1)
        recorrentes_futuras = conn.execute(
            "SELECT COALESCE(SUM(valor),0) FROM transacoes "
            "WHERE recorrente=1 AND tipo='despesa' AND data LIKE ? AND substr(data,9,2) > ?",
            (f"{prefixo_mes}%", f"{hoje.day:02d}"),
        ).fetchone()[0]
        valor_hoje = max(0, (rec_mes - desp_mes - simples_mes - recorrentes_futuras) / dias_restantes)
        
        # Calcular % da receita gasta
        pct_gasto = (desp_mes / rec_mes * 100) if rec_mes > 0 else 0
        cor_hoje = "#00d4aa" if valor_hoje > 30 else ("#f59e0b" if valor_hoje > 10 else "#ff4b6e")
        emoji_hoje = "😎" if valor_hoje > 50 else ("🙂" if valor_hoje > 20 else "😬")
        nivel = "Tranquilo" if valor_hoje > 50 else ("Cuidado" if valor_hoje > 20 else "Aperto")
        
        # Ring progress para % gasto
        ring_html = ring_progress(min(pct_gasto, 100), size=65, stroke=5, 
                                   color=cor_hoje, label=f"{pct_gasto:.0f}%")
        
        st.markdown(f"""
            <div class="glass-card" style="margin-bottom:1.2rem; border-left: 4px solid {cor_hoje};">
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:1rem;">
                    <div style="flex:1;min-width:200px;">
                        <div style="font-size:0.68rem; color:var(--text2); text-transform:uppercase; letter-spacing:0.8px; font-weight:600;">
                            💡 Quanto posso gastar hoje
                        </div>
                        <div style="display:flex;align-items:baseline;gap:0.5rem;margin:0.3rem 0;">
                            <span style="font-size:2rem; font-weight:900; color:{cor_hoje};">{fmt(valor_hoje)}</span>
                            <span style="font-size:1.3rem;">{emoji_hoje}</span>
                        </div>
                        <div style="display:flex;align-items:center;gap:0.4rem;">
                            <span style="display:inline-block;padding:0.15rem 0.5rem;background:{'var(--green-glow)' if nivel == 'Tranquilo' else ('var(--amber-glow)' if nivel == 'Cuidado' else 'var(--red-glow)')};
                                color:{cor_hoje};font-size:0.65rem;font-weight:700;border-radius:10px;">
                                {'🟢' if nivel == 'Tranquilo' else ('🟡' if nivel == 'Cuidado' else '🔴')} {nivel}
                            </span>
                        </div>
                        <div style="font-size:0.68rem; color:var(--text3); margin-top:0.4rem;">
                            Faltam {dias_restantes} dias · Sobra total: {fmt(rec_mes - desp_mes - simples_mes)} · Fixas pendentes: {fmt(recorrentes_futuras)}
                        </div>
                    </div>
                    <div style="flex-shrink:0;text-align:center;">
                        {ring_html}
                        <div style="font-size:0.58rem;color:var(--text3);margin-top:0.3rem;">da receita<br>já usada</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════
    # CARDS KPI COM TRENDS
    # ══════════════════════════════════════════════════════════════════
    sec("📈", f"Resumo de {MESES_PT[mes_sel]}")
    
    # Calcular trends vs mês anterior
    def calc_trend(atual, anterior):
        if anterior > 0:
            pct = ((atual - anterior) / anterior) * 100
            return f"{abs(pct):.0f}%", "up" if pct > 0 else "down"
        return None, "neutral"
    
    trend_rec, dir_rec = calc_trend(rec_mes, rec_ant)
    trend_desp, dir_desp = calc_trend(desp_mes, desp_ant)
    
    b_cls = "mv-green" if balanco_mes >= 0 else "mv-red"
    b_bdg = "mb-green" if balanco_mes >= 0 else "mb-red"

    html_cards = f"""
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(165px, 1fr)); gap: 0.8rem; margin-bottom: 1rem;">
        <div>{metric_card("💵","green","Receitas",fmt(rec_mes),"mv-green","Entradas","mb-green", trend_rec, dir_rec)}</div>
        <div>{metric_card("💳","red","Despesas",fmt(desp_mes),"mv-red","Saídas","mb-red", trend_desp, "down" if dir_desp=="up" else "up" if dir_desp=="down" else "neutral")}</div>
        <div>{metric_card("📋","amber","Simples Nacional" + get_tooltip("simples"),fmt(simples_mes),"mv-amber","6% s/ receita","mb-amber")}</div>
        <div>{metric_card("📊","purple","Balanço Líquido" + get_tooltip("balanco"),fmt(balanco_mes),b_cls,"Superávit" if balanco_mes>=0 else "Déficit",b_bdg)}</div>
        <div>{metric_card("💰","blue","Saldo do Mês",fmt(saldo_total),"mv-blue","Livre este mês","mb-blue")}</div>
    </div>
    """
    st.markdown(html_cards, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════
    # EVOLUÇÃO DIÁRIA + DESPESAS POR CATEGORIA (lado a lado)
    # ══════════════════════════════════════════════════════════════════
    sec("📈", "Evolução do Saldo no Mês")
    from core.models import get_agrupamento_diario_mes
    dados_diarios = get_agrupamento_diario_mes(conn, prefixo_mes)
    dict_diario = {int(r[0]): {"rec": r[1], "desp": r[2]} for r in dados_diarios}
    
    datas, saldos_dia, acum = [], [], 0
    for d in range(1, dias_mes + 1):
        dia_info = dict_diario.get(d, {"rec": 0, "desp": 0})
        r = dia_info["rec"]
        de = dia_info["desp"]
        acum += r - de
        datas.append(d)
        saldos_dia.append(acum)
    
    fig_l = go.Figure()
    # Área de fundo
    fig_l.add_trace(go.Scatter(
        x=datas, y=saldos_dia, mode="lines",
        line=dict(color="rgba(78,140,255,0)", width=0),
        fill="tozeroy", fillcolor="rgba(78,140,255,0.06)",
        showlegend=False, hoverinfo="skip",
    ))
    # Linha principal
    fig_l.add_trace(go.Scatter(
        x=datas, y=saldos_dia, mode="lines+markers",
        line=dict(color="#4e8cff", width=2.5, shape="spline"),
        marker=dict(size=4, color="#4e8cff", line=dict(width=1, color="#0b0e14")),
        hovertemplate="Dia %{x}<br>Saldo: R$ %{y:,.2f}<extra></extra>",
        name="Saldo",
    ))
    fig_l.update_layout(
        **PLOTLY_LAYOUT, height=220,
        xaxis=dict(title="Dia", showgrid=False, dtick=5),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.03)",
                   zeroline=True, zerolinecolor="rgba(255,75,110,0.3)"),
    )
    st.plotly_chart(fig_l, key="line_d")

    # ── Gráficos ──────────────────────────────────────────────────────
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        sec("🍩", "Despesas por Categoria")
        dpc = read_sql(
            "SELECT c.nome, c.icone, SUM(t.valor) as total FROM transacoes t "
            "JOIN categorias c ON t.categoria_id=c.id WHERE t.tipo='despesa' AND t.data LIKE ? "
            "GROUP BY c.id ORDER BY total DESC",
            conn, params=(f"{prefixo_mes}%",),
        )
        if not dpc.empty:
            cores = ["#ff4b6e", "#f59e0b", "#4e8cff", "#a855f7", "#00d4aa",
                     "#ef4444", "#06b6d4", "#ec4899", "#84cc16", "#f97316"]
            fig_p = go.Figure(go.Pie(
                labels=[f"{r['icone']} {r['nome']}" for _, r in dpc.iterrows()],
                values=dpc["total"], hole=0.65,
                marker=dict(colors=cores[:len(dpc)], line=dict(color="#0b0e14", width=2)),
                textinfo="percent",
                textfont=dict(size=11, color="#f0f2f5"),
                hovertemplate="<b>%{label}</b><br>R$ %{value:,.2f}<extra></extra>",
            ))
            fig_p.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter", color="#8b95a5"),
                margin=dict(l=25, r=25, t=40, b=25),
                showlegend=True, height=340,
                legend=dict(font=dict(size=9, color="#8b95a5"), bgcolor="rgba(0,0,0,0)", y=0.5, x=1.02),
                annotations=[dict(text=f"<b>{fmt(desp_mes)}</b>", x=0.5, y=0.5,
                                   font=dict(size=12, color="#f0f2f5"), showarrow=False)],
            )
            st.plotly_chart(fig_p, key="pie_d")
        else:
            st.info("Sem despesas neste mês.")

    with col_g2:
        sec("📊", "Receitas vs Despesas (6 meses)")
        from core.models import get_agrupamento_mensal_ano
        
        meses_ano_atual = get_agrupamento_mensal_ano(conn, ano_sel)
        dict_mensal_atual = {int(r[0]): {"rec": r[1], "desp": r[2]} for r in meses_ano_atual}
        
        ano_anterior = ano_sel - 1
        meses_ano_ant = get_agrupamento_mensal_ano(conn, ano_anterior)
        dict_mensal_ant = {int(r[0]): {"rec": r[1], "desp": r[2]} for r in meses_ano_ant}

        ml, rv, dv = [], [], []
        for i in range(5, -1, -1):
            p, m2, a2 = get_pref(mes_sel - i, ano_sel)
            ml.append(MESES_PT[m2][:3])
            if a2 == ano_sel:
                dados_mes = dict_mensal_atual.get(m2, {"rec": 0, "desp": 0})
            else:
                dados_mes = dict_mensal_ant.get(m2, {"rec": 0, "desp": 0})
            rv.append(dados_mes["rec"])
            dv.append(dados_mes["desp"])
        
        fig_b = go.Figure()
        fig_b.add_trace(go.Bar(x=ml, y=rv, name="Receitas", marker=dict(color="#00d4aa", cornerradius=6)))
        fig_b.add_trace(go.Bar(x=ml, y=dv, name="Despesas", marker=dict(color="#ff4b6e", cornerradius=6)))
        fig_b.update_layout(
            **PLOTLY_LAYOUT, barmode="group", height=340,
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.03)"),
            xaxis=dict(showgrid=False, tickangle=0),
        )
        st.plotly_chart(fig_b, key="bar_d")

    # ══════════════════════════════════════════════════════════════════
    # CALENDÁRIO HEATMAP + FEED DE ATIVIDADE (lado a lado)
    # ══════════════════════════════════════════════════════════════════
    col_cal, col_feed = st.columns([3, 2])
    
    with col_cal:
        sec("📅", "Calendário de Gastos")
        
        # Buscar gastos por dia
        gastos_por_dia = {}
        for row in dados_diarios:
            dia = int(row[0])
            gastos_por_dia[dia] = row[2]  # desp
        
        # Buscar dias com contas a pagar (recorrentes)
        dias_com_conta = set()
        if hoje.month == mes_sel and hoje.year == ano_sel:
            recorrentes = conn.execute(
                "SELECT substr(data,9,2) FROM transacoes WHERE recorrente=1 AND tipo='despesa'"
            ).fetchall()
            for r in recorrentes:
                try:
                    dias_com_conta.add(int(r[0]))
                except Exception:
                    pass
        
        max_gasto = max(gastos_por_dia.values()) if gastos_por_dia else 1
        
        # Montar grid do calendário
        import datetime
        primeiro_dia = datetime.date(ano_sel, mes_sel, 1)
        offset = primeiro_dia.weekday()  # 0=Monday
        
        cal_html = '<div class="cal-grid">'
        # Headers
        for dia_semana in ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]:
            cal_html += f'<div class="cal-header">{dia_semana}</div>'
        
        # Empty cells antes do dia 1
        for _ in range(offset):
            cal_html += calendar_day_cell(0, is_empty=True)
        
        # Dias do mês
        for d in range(1, dias_mes + 1):
            gasto = gastos_por_dia.get(d, 0)
            is_today = (d == hoje.day and mes_sel == hoje.month and ano_sel == hoje.year)
            has_bill = d in dias_com_conta and (d >= hoje.day if hoje.month == mes_sel else True)
            cal_html += calendar_day_cell(d, gasto, max_gasto, is_today, has_bill)
        
        cal_html += '</div>'
        
        # Legenda
        cal_html += """
        <div style="display:flex;align-items:center;gap:0.8rem;margin-top:0.6rem;justify-content:center;">
            <div style="display:flex;align-items:center;gap:0.3rem;">
                <div style="width:10px;height:10px;border-radius:3px;background:rgba(11,14,20,0.5);border:1px solid var(--border);"></div>
                <span style="font-size:0.58rem;color:var(--text3);">Sem gasto</span>
            </div>
            <div style="display:flex;align-items:center;gap:0.3rem;">
                <div style="width:10px;height:10px;border-radius:3px;background:rgba(255,75,110,0.45);"></div>
                <span style="font-size:0.58rem;color:var(--text3);">Gasto alto</span>
            </div>
            <div style="display:flex;align-items:center;gap:0.3rem;">
                <div style="width:5px;height:5px;border-radius:50%;background:var(--red);"></div>
                <span style="font-size:0.58rem;color:var(--text3);">Conta a pagar</span>
            </div>
        </div>
        """
        
        st.markdown(cal_html, unsafe_allow_html=True)
    
    with col_feed:
        sec("⚡", "Atividade Recente")
        
        # Últimas 5 transações
        ultimas = read_sql(
            "SELECT t.descricao, t.valor, t.tipo, t.data, c.icone, c.nome as cat "
            "FROM transacoes t LEFT JOIN categorias c ON t.categoria_id=c.id "
            "WHERE t.data LIKE ? ORDER BY t.data DESC, t.id DESC LIMIT 5",
            conn, params=(f"{prefixo_mes}%",),
        )
        
        if not ultimas.empty:
            feed_html = '<div class="activity-feed">'
            for _, row in ultimas.iterrows():
                is_inc = row["tipo"] == "receita"
                icone = row["icone"] if pd.notna(row["icone"]) else "📌"
                cat = row["cat"] if pd.notna(row["cat"]) else ""
                from core.utils import fmt_data_pt
                data_fmt = fmt_data_pt(str(row["data"]))
                feed_html += activity_item(
                    icone, str(row["descricao"]),
                    f"{cat} · {data_fmt}",
                    fmt(row["valor"]), is_inc,
                )
            feed_html += '</div>'
            st.markdown(feed_html, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div class="empty-state" style="padding:1.5rem;">
                    <div class="empty-icon">📝</div>
                    <div class="empty-title">Sem atividade</div>
                    <div class="empty-desc">Registre suas primeiras transações na aba Transações</div>
                </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════
    # PROJEÇÃO DE FLUXO DE CAIXA
    # ══════════════════════════════════════════════════════════════════
    if hoje.month == mes_sel and hoje.year == ano_sel:
        sec("📈", "Projeção de Saldo (Próximos 30 dias)")
        st.caption("Evolução do seu saldo bancário baseada em contas fixas, faturas e lançamentos futuros.")
        
        import datetime
        datas_futuras = [hoje + datetime.timedelta(days=i) for i in range(31)]
        saldos_projetados = []
        saldo_simulado = saldo_total
        
        tx_futuras_db = conn.execute(
            "SELECT data, valor, tipo FROM transacoes WHERE data > ?", (hoje.strftime("%Y-%m-%d"),)
        ).fetchall()
        tx_futuras_dict = {}
        for d, v, t in tx_futuras_db:
            if d not in tx_futuras_dict: tx_futuras_dict[d] = 0
            tx_futuras_dict[d] += v if t == 'receita' else -v
            
        recorrentes = conn.execute(
            "SELECT t.id, t.descricao, t.valor, t.data, c.icone "
            "FROM transacoes t LEFT JOIN categorias c ON t.categoria_id = c.id "
            "WHERE t.recorrente=1 AND t.tipo='despesa'"
        ).fetchall()

        mes_atual = hoje.month
        ano_atual = hoje.year
        mes_prox = mes_atual + 1 if mes_atual < 12 else 1
        ano_prox = ano_atual if mes_atual < 12 else ano_atual + 1
        
        pagas_db = conn.execute(
            "SELECT descricao, substr(data, 6, 2) FROM transacoes "
            "WHERE tipo = 'despesa' AND (data LIKE ? OR data LIKE ?)",
            (f"{ano_atual}-{mes_atual:02d}%", f"{ano_prox}-{mes_prox:02d}%")
        ).fetchall()
        pagas_set = {(r[0], int(r[1])) for r in pagas_db}

        for dia_data in datas_futuras:
            str_data = dia_data.strftime("%Y-%m-%d")
            if str_data in tx_futuras_dict:
                saldo_simulado += tx_futuras_dict[str_data]
            for r in recorrentes:
                dia_vencimento = int(r[3][-2:])
                if dia_data.day == dia_vencimento:
                    if (r[1], dia_data.month) not in pagas_set or dia_data.month != hoje.month:
                        saldo_simulado -= r[2]
            saldos_projetados.append(saldo_simulado)
            
        fig_proj = go.Figure()
        fig_proj.add_trace(go.Scatter(
            x=datas_futuras, y=saldos_projetados, 
            mode='lines', name='Saldo Projetado',
            line=dict(color='#00d4aa', width=3, shape='spline'),
            fill='tozeroy', fillcolor='rgba(0, 212, 170, 0.08)'
        ))
        
        layout_kwargs = PLOTLY_LAYOUT.copy()
        layout_kwargs["margin"] = dict(l=0, r=0, t=10, b=0)
        layout_kwargs["height"] = 250
        
        fig_proj.update_layout(
            **layout_kwargs,
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.03)", zeroline=True, zerolinecolor="rgba(255,255,255,0.1)"), 
            xaxis=dict(showgrid=False, tickformat="%d/%m")
        )
        st.plotly_chart(fig_proj, width='stretch')
        st.markdown("<br>", unsafe_allow_html=True)
    

    # ══════════════════════════════════════════════════════════════════
    # SAÚDE FINANCEIRA + REGRA 50-30-20
    # ══════════════════════════════════════════════════════════════════
    with st.expander("💚 Saúde Financeira e Regra 50-30-20", expanded=False):
        col_sc, col_rule = st.columns(2)

        with col_sc:
            sec("💚", "Saúde Financeira", tooltip="score")
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=score,
                number=dict(font=dict(size=48, color="#f0f2f5")),
                gauge=dict(
                    axis=dict(range=[0, 100], tickcolor="#5a6478", tickfont=dict(color="#5a6478")),
                    bar=dict(color=score_cor, thickness=0.3),
                    bgcolor="rgba(255,255,255,0.04)",
                    borderwidth=0,
                    steps=[
                        dict(range=[0, 40], color="rgba(255,75,110,0.08)"),
                        dict(range=[40, 70], color="rgba(245,158,11,0.08)"),
                        dict(range=[70, 100], color="rgba(0,212,170,0.08)"),
                    ],
                    threshold=dict(line=dict(color="#fff", width=2), thickness=0.8, value=score),
                ),
                title=dict(text=f"<b>{score_label}</b>", font=dict(size=14, color=score_cor)),
            ))
            fig_gauge.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", font=dict(family="Inter"),
                height=250, margin=dict(l=30, r=30, t=60, b=10),
            )
            st.plotly_chart(fig_gauge, key="gauge_score")

        with col_rule:
            sec("📐", "Regra 50-30-20", tooltip="regra503020")
            regra = calcular_50_30_20(conn, prefixo_mes, rec_mes)
            items = [
                ("🏠 Necessidades", regra["necessidades"], "#4e8cff"),
                ("🎮 Desejos", regra["desejos"], "#a855f7"),
                ("💰 Prioridades", regra["prioridades"], "#00d4aa"),
            ]
            for nome, data, cor in items:
                pct = min(data["pct"], 100)
                ideal_pos = data["ideal"]
                status = "✅" if data["pct"] <= data["ideal"] + 5 else "⚠️"
                st.markdown(f"""
                    <div class="rule-bar-wrap">
                        <div class="rule-bar-label">
                            <span class="rule-bar-name">{nome} {status}</span>
                            <span class="rule-bar-vals">{int(data['pct'])}% real &middot; {data['ideal']}% ideal &middot; {fmt(data['valor'])}</span>
                        </div>
                        <div class="rule-bar-bg">
                            <div class="rule-bar-fill" style="width:{pct}%; background: {cor};"></div>
                            <div class="rule-bar-ideal" style="left:{ideal_pos}%;"></div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

            if rec_mes > 0:
                pct_livre = max(0, 100 - regra["necessidades"]["pct"] - regra["desejos"]["pct"])
                valor_livre = max(0, (rec_mes * pct_livre / 100) - simples_mes)
                st.markdown(f"""
                    <div style="background: rgba(0,212,170,0.06); border: 1px solid rgba(0,212,170,0.15); border-radius: 10px; padding: 0.7rem 1rem; margin-top: 0.5rem;">
                        <span style="font-size: 0.78rem; color: #8b95a5;">Disponível para investir/guardar:</span>
                        <span style="font-size: 0.92rem; font-weight: 700; color: #00d4aa; float: right;">{fmt(valor_livre)}</span>
                    </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════
    # CONQUISTAS E ATALHOS
    # ══════════════════════════════════════════════════════════════════
    with st.expander("🏅 Conquistas e ⚡ Atalhos Rápidos", expanded=False):
        # ── Gamificação (Streaks e Badges) ──────────────────────────────
        from components.cards import streak_bar
        
        # Calcular Streak (Dias seguidos com transações)
        datas_tx = conn.execute("SELECT DISTINCT data FROM transacoes ORDER BY data DESC").fetchall()
        streak = 0
        if datas_tx:
            datas_str = [r[0] for r in datas_tx]
            from datetime import date, timedelta
            import datetime
            hoje_str = date.today().strftime("%Y-%m-%d")
            ontem_str = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
            
            # O streak começa se a última tx for hoje ou ontem
            if datas_str and (datas_str[0] == hoje_str or datas_str[0] == ontem_str):
                streak = 1
                curr_date = datetime.datetime.strptime(datas_str[0], "%Y-%m-%d").date()
                for d_str in datas_str[1:]:
                    d_date = datetime.datetime.strptime(d_str, "%Y-%m-%d").date()
                    if (curr_date - d_date).days == 1:
                        streak += 1
                        curr_date = d_date
                    else:
                        break
                        
        if streak > 0:
            st.markdown(streak_bar(streak, "dias seguidos registrando!"), unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

        badges_ganhas = []
    
        if (rec_mes - desp_mes - simples_mes) > 0 and desp_mes > 0:
            badges_ganhas.append(("💰", "Poupador", "Fechando o mês no azul", "#4e8cff"))
        
        saldo_reserva_local = ctx.get("saldo_reserva", 0)
        if saldo_reserva_local > 0 and desp_mes > 0 and (saldo_reserva_local / desp_mes) >= 3:
            badges_ganhas.append(("🛡️", "Blindado", "+3 meses de reserva", "#a855f7"))
        
        aportes = conn.execute(
            "SELECT COUNT(*) FROM transacoes t JOIN contas c ON t.conta_id = c.id "
            "WHERE c.tipo = 'Corretora/Investimento' AND t.tipo = 'despesa' AND t.data LIKE ?",
            (f"{prefixo_mes}%",)
        ).fetchone()[0]
        if aportes > 0:
            badges_ganhas.append(("📈", "Investidor", "Aportou neste mês", "#00d4aa"))
        
        # Badges extras
        if score >= 80:
            badges_ganhas.append(("🌟", "Finanças de Elite", f"Score {score}/100", "#f59e0b"))
        
        total_txs_mes = conn.execute(
            "SELECT COUNT(id) FROM transacoes WHERE data LIKE ?", (f"{prefixo_mes}%",)
        ).fetchone()[0]
        if total_txs_mes >= 20:
            badges_ganhas.append(("📋", "Detalhista", f"{total_txs_mes} registros no mês", "#06b6d4"))

        if badges_ganhas:
            sec("🏅", "Suas Conquistas")
            badges_html = '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:0.6rem;">'
            for emoji, titulo, desc, cor in badges_ganhas:
                badges_html += badge_card(emoji, titulo, desc, cor)
            badges_html += '</div>'
            st.markdown(badges_html, unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

        # ── Atalhos de Lançamento ──────────────────────────────────────
        sec("⚡", "Lançamento Rápido")
        atalhos = conn.execute(
            "SELECT a.id, a.descricao, a.valor, a.icone, a.tipo, c.nome, co.nome, a.categoria_id, a.conta_id "
            "FROM atalhos a LEFT JOIN categorias c ON a.categoria_id = c.id "
            "LEFT JOIN contas co ON a.conta_id = co.id"
        ).fetchall()
    
        if atalhos:
            cols_at = st.columns(min(len(atalhos) + 1, 6))
            for i, a in enumerate(atalhos):
                with cols_at[i % 6]:
                    if st.button(f"{a[3]}\n{a[1]}", key=f"btn_at_{a[0]}", help=f"{fmt(a[2])} em {a[6]}"):
                        conn.execute(
                            "INSERT INTO transacoes (tipo,descricao,valor,data,categoria_id,conta_id) "
                            "VALUES (?,?,?,?,?,?)",
                            (a[4], a[1], a[2], hoje.strftime("%Y-%m-%d"), a[7], a[8])
                        )
                        conn.commit()
                        from core.models import clear_cache_transacoes
                        clear_cache_transacoes()
                        st.success(f"Lançamento de {fmt(a[2])} adicionado!")
                        st.rerun()
        
            with cols_at[len(atalhos) % 6]:
                with st.popover("⚙️ Gerenciar"):
                    st.write("Adicionar Novo Atalho")
                    with st.form("form_novo_atalho", clear_on_submit=True):
                        nat_desc = st.text_input("Descrição", placeholder="Ex: Cafezinho")
                        nat_val = st.number_input("Valor", min_value=0.1, step=1.0)
                        nat_ic = st.selectbox("Ícone", ["☕", "🚗", "🍔", "💊", "📱", "🍺", "🎫"])
                    
                        cats_disp = {f"{r[1]} {r[2]}": r[0] for r in conn.execute("SELECT id, icone, nome FROM categorias").fetchall()}
                        conts_disp = {f"{r[1]} {r[2]}": r[0] for r in conn.execute("SELECT id, icone, nome FROM contas").fetchall()}
                    
                        if cats_disp and conts_disp:
                            nat_cat = st.selectbox("Categoria", list(cats_disp.keys()))
                            nat_conta = st.selectbox("Conta", list(conts_disp.keys()))
                    
                        if st.form_submit_button("Salvar Atalho") and cats_disp and conts_disp:
                            conn.execute(
                                "INSERT INTO atalhos (descricao,valor,categoria_id,conta_id,icone,tipo) VALUES (?,?,?,?,?,?)",
                                (nat_desc, nat_val, cats_disp[nat_cat], conts_disp[nat_conta], nat_ic, "despesa")
                            )
                            conn.commit()
                            st.rerun()
                
                    st.write("Atalhos Existentes")
                    for a in atalhos:
                        ca1, ca2 = st.columns([4,1])
                        with ca1:
                            st.write(f"{a[3]} {a[1]} - {fmt(a[2])}")
                        with ca2:
                            if st.button("🗑️", key=f"del_at_{a[0]}"):
                                conn.execute("DELETE FROM atalhos WHERE id=?", (a[0],))
                                conn.commit()
                                st.rerun()
        else:
            st.markdown("""
                <div class="empty-state" style="padding:1.5rem;">
                    <div class="empty-icon">⚡</div>
                    <div class="empty-title">Sem atalhos ainda</div>
                    <div class="empty-desc">Crie atalhos para lançar despesas frequentes com um clique.</div>
                </div>
            """, unsafe_allow_html=True)
            with st.expander("➕ Criar Primeiro Atalho"):
                with st.form("form_primeiro_atalho"):
                    nat_desc = st.text_input("Descrição", placeholder="Ex: Uber")
                    nat_val = st.number_input("Valor Padrão", min_value=0.1, step=1.0, value=20.0)
                    nat_ic = st.selectbox("Ícone", ["🚗", "☕", "🍔", "💊", "📱", "🍺", "🎫"])
                
                    cats_disp = {f"{r[1]} {r[2]}": r[0] for r in conn.execute("SELECT id, icone, nome FROM categorias").fetchall()}
                    conts_disp = {f"{r[1]} {r[2]}": r[0] for r in conn.execute("SELECT id, icone, nome FROM contas").fetchall()}
                
                    if cats_disp and conts_disp:
                        nat_cat = st.selectbox("Categoria", list(cats_disp.keys()))
                        nat_conta = st.selectbox("Conta", list(conts_disp.keys()))
                
                    if st.form_submit_button("Salvar Atalho") and cats_disp and conts_disp:
                        conn.execute(
                            "INSERT INTO atalhos (descricao,valor,categoria_id,conta_id,icone,tipo) VALUES (?,?,?,?,?,?)",
                            (nat_desc, nat_val, cats_disp[nat_cat], conts_disp[nat_conta], nat_ic, "despesa")
                        )
                        conn.commit()
                        st.rerun()


    # ══════════════════════════════════════════════════════════════════
    # PREVISÃO DE CONTAS + TOP 5 + VISÃO ANUAL
    # ══════════════════════════════════════════════════════════════════
    with st.expander("📅 Previsão de Contas a Pagar", expanded=False):
        sec("📅", "Próximos Vencimentos")
        recorrentes = conn.execute(
            "SELECT t.id, t.descricao, t.valor, t.data, c.icone "
            "FROM transacoes t LEFT JOIN categorias c ON t.categoria_id = c.id "
            "WHERE t.recorrente=1 AND t.tipo='despesa' "
            "ORDER BY substr(t.data,9,2) ASC"
        ).fetchall()
    
        if recorrentes:
            futuras = [r for r in recorrentes if int(r[3][-2:]) >= hoje.day]
            if futuras:
                for r in futuras:
                    dia_vencimento = int(r[3][-2:])
                    dias_falta = dia_vencimento - hoje.day
                    status_venc = "Hoje!" if dias_falta == 0 else f"Faltam {dias_falta} dias"
                    cor_venc = "#ff4b6e" if dias_falta <= 3 else "#f59e0b" if dias_falta <= 7 else "#00d4aa"
                
                    st.markdown(f"""
                    <div class="alert-card" style="border-color:{cor_venc};">
                        <div style="display:flex;align-items:center;gap:0.8rem;flex:1;">
                            <div style="font-size:1.5rem;">{r[4] or '📌'}</div>
                            <div>
                                <div style="font-weight:600; font-size:0.9rem;">{r[1]}</div>
                                <div style="font-size:0.7rem; color:{cor_venc};">{status_venc} (Dia {dia_vencimento})</div>
                            </div>
                        </div>
                        <div style="font-weight:700; color:#ff4b6e;">- {fmt(r[2])}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("Nenhuma conta fixa para vencer nos próximos dias deste mês! 🎉")
        else:
            st.info("Nenhuma conta recorrente cadastrada.")
    
        st.markdown("<br>", unsafe_allow_html=True)
    

    with st.expander("🏆 Top 5 Gastos e Visão Anual", expanded=False):
        col_top, col_annual = st.columns(2)

        with col_top:
            sec("🏆", "Top 5 Gastos do Mês")
            top5 = read_sql(
                "SELECT t.descricao, t.valor, t.data, c.icone, c.nome as cat "
                "FROM transacoes t LEFT JOIN categorias c ON t.categoria_id=c.id "
                "WHERE t.tipo='despesa' AND t.data LIKE ? "
                "ORDER BY t.valor DESC LIMIT 5",
                conn, params=(f"{prefixo_mes}%",),
            )
            if not top5.empty:
                rank_icons = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
                for i, (_, row) in enumerate(top5.iterrows()):
                    pct_rec = (row["valor"] / rec_mes * 100) if rec_mes > 0 else 0
                    st.markdown(f"""
                        <div class="top-exp">
                            <div class="top-exp-left">
                                <div class="top-exp-rank">{rank_icons[i]}</div>
                                <div>
                                    <div class="top-exp-name">{row['icone'] or '📌'} {html.escape(row['descricao'])}</div>
                                    <div style="font-size:0.65rem;color:#5a6478;">{html.escape(row['cat']) if row['cat'] else ''} · {row['data']}</div>
                                </div>
                            </div>
                            <div>
                                <div class="top-exp-val">{fmt(row['valor'])}</div>
                                <div style="font-size:0.6rem;color:#5a6478;text-align:right;">{pct_rec:.1f}% da receita</div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("Sem gastos neste mês.")

        with col_annual:
            sec("📅", f"Visão Anual {ano_sel}")
            ml_ano, rv_ano, dv_ano = [], [], []
            total_rec_ano, total_desp_ano = 0, 0
        
            meses_ano_atual_total = get_agrupamento_mensal_ano(conn, ano_sel)
            dict_mensal_total = {int(r[0]): {"rec": r[1], "desp": r[2]} for r in meses_ano_atual_total}
        
            for m in range(1, 13):
                dados_mes = dict_mensal_total.get(m, {"rec": 0, "desp": 0})
                r_val = dados_mes["rec"]
                d_val = dados_mes["desp"]
            
                ml_ano.append(MESES_PT[m][:3])
                rv_ano.append(r_val)
                dv_ano.append(d_val)
                total_rec_ano += r_val
                total_desp_ano += d_val

            saldo_acumulado = []
            acc = 0
            melhor_mes = None
            pior_mes = None
            melhor_saldo = -float('inf')
            pior_saldo = float('inf')
        
            for m_idx, (r, d) in enumerate(zip(rv_ano, dv_ano)):
                saldo_mes = r - d
                if r > 0 or d > 0:
                    if saldo_mes > melhor_saldo:
                        melhor_saldo = saldo_mes
                        melhor_mes = ml_ano[m_idx]
                    if saldo_mes < pior_saldo:
                        pior_saldo = saldo_mes
                        pior_mes = ml_ano[m_idx]
                acc += saldo_mes
                saldo_acumulado.append(acc)

            fig_ano = go.Figure()
            fig_ano.add_trace(go.Bar(x=ml_ano, y=rv_ano, name="Receitas", marker=dict(color="#00d4aa", cornerradius=4)))
            fig_ano.add_trace(go.Bar(x=ml_ano, y=dv_ano, name="Despesas", marker=dict(color="#ff4b6e", cornerradius=4)))
            fig_ano.add_trace(go.Scatter(x=ml_ano, y=saldo_acumulado, name="Saldo Acum.", mode='lines+markers', line=dict(color="#4e8cff", width=2)))
        
            fig_ano.update_layout(
                **PLOTLY_LAYOUT, barmode="group", height=250,
                yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.03)"),
                xaxis=dict(showgrid=False, tickangle=0),
            )
            st.plotly_chart(fig_ano, key="bar_anual")

            media_mensal = total_desp_ano / max(mes_sel, 1)
            melhor_str = f"{melhor_mes} ({fmt(melhor_saldo)})" if melhor_mes else "-"
            pior_str = f"{pior_mes} ({fmt(pior_saldo)})" if pior_mes else "-"
        
            st.markdown(f"""
                <div style="display:flex;gap:0.8rem;flex-wrap:wrap; margin-bottom: 1rem;">
                    <div class="glass-card" style="flex:1;text-align:center;padding:0.7rem;">
                        <div style="font-size:0.62rem;color:#8b95a5;text-transform:uppercase;">Receita Anual</div>
                        <div style="font-size:0.95rem;font-weight:800;color:#00d4aa;">{fmt(total_rec_ano)}</div>
                    </div>
                    <div class="glass-card" style="flex:1;text-align:center;padding:0.7rem;">
                        <div style="font-size:0.62rem;color:#8b95a5;text-transform:uppercase;">Despesa Anual</div>
                        <div style="font-size:0.95rem;font-weight:800;color:#ff4b6e;">{fmt(total_desp_ano)}</div>
                    </div>
                    <div class="glass-card" style="flex:1;text-align:center;padding:0.7rem;">
                        <div style="font-size:0.62rem;color:#8b95a5;text-transform:uppercase;">Média/Mês</div>
                        <div style="font-size:0.95rem;font-weight:800;color:#f59e0b;">{fmt(media_mensal)}</div>
                    </div>
                </div>
                <div style="display:flex;gap:0.8rem;flex-wrap:wrap;">
                    <div class="glass-card" style="flex:1;text-align:center;padding:0.7rem;">
                        <div style="font-size:0.62rem;color:#8b95a5;text-transform:uppercase;">Melhor Mês</div>
                        <div style="font-size:0.85rem;font-weight:800;color:#00d4aa;">{melhor_str}</div>
                    </div>
                    <div class="glass-card" style="flex:1;text-align:center;padding:0.7rem;">
                        <div style="font-size:0.62rem;color:#8b95a5;text-transform:uppercase;">Pior Mês</div>
                        <div style="font-size:0.85rem;font-weight:800;color:#ff4b6e;">{pior_str}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
