"""
tabs/dashboard.py — Aba principal do Dashboard.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import html
import calendar

from core.utils import fmt, get_pref, MESES_PT, PLOTLY_LAYOUT
from core.database import read_sql
from components.cards import metric_card, sec
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

    # ── Alertas Inteligentes (Fase 4.2) ───────────────────────────────
    alertas = []
    
    # Alerta 1: Despesas altas
    if rec_mes > 0 and (desp_mes / rec_mes) > 0.8:
        alertas.append(("🚨", "Atenção: Suas despesas já ultrapassaram 80% da receita deste mês!", "#ff4b6e"))
        
    # Alerta 2: Dinheiro parado
    if balanco_mes > 500:
        alertas.append(("💡", f"Você tem {fmt(balanco_mes)} sobrando este mês. Que tal guardar na Reserva?", "#00d4aa"))
        
    # Alerta 3: Recorrentes pendentes (se for o mês atual)
    if hoje.month == mes_sel and hoje.year == ano_sel:
        recorrentes_count = conn.execute(
            "SELECT COUNT(id) FROM transacoes WHERE recorrente=1 AND tipo='despesa' AND data LIKE ? AND substr(data,9,2) > ?",
            (f"{prefixo_mes}%", f"{hoje.day:02d}")
        ).fetchone()[0]
        if recorrentes_count > 0:
            alertas.append(("⏰", f"Você tem {recorrentes_count} transações recorrentes previstas para os próximos dias.", "#f59e0b"))

    if alertas:
        for icone, msg, cor in alertas:
            st.markdown(f"""
                <div style="background:rgba(255,255,255,0.02); border-left:3px solid {cor}; padding:0.6rem 1rem; border-radius:6px; margin-bottom:0.5rem; display:flex; align-items:center; gap:0.5rem; animation: slideUp 0.3s ease-out forwards;">
                    <span style="font-size:1.1rem;">{icone}</span>
                    <span style="font-size:0.8rem; color:#f0f2f5;">{msg}</span>
                </div>
            """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

    # ── Widget: Quanto posso gastar hoje (Fase 3.5) ───────────────────
    if rec_mes > 0 and hoje.month == mes_sel and hoje.year == ano_sel:
        dias_restantes = max(dias_mes - hoje.day, 1)
        recorrentes_futuras = conn.execute(
            "SELECT COALESCE(SUM(valor),0) FROM transacoes "
            "WHERE recorrente=1 AND tipo='despesa' AND data LIKE ? AND substr(data,9,2) > ?",
            (f"{prefixo_mes}%", f"{hoje.day:02d}"),
        ).fetchone()[0]
        valor_hoje = max(0, (rec_mes - desp_mes - simples_mes - recorrentes_futuras) / dias_restantes)
        cor_hoje = "#00d4aa" if valor_hoje > 30 else ("#f59e0b" if valor_hoje > 10 else "#ff4b6e")
        emoji_hoje = "😎" if valor_hoje > 50 else ("🙂" if valor_hoje > 20 else "😬")
        st.markdown(f"""
            <div class="glass-card" style="margin-bottom:1.2rem; border-left: 4px solid {cor_hoje}; background: linear-gradient(135deg, rgba(22,27,38,0.9), rgba(22,27,38,0.6));">
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:1rem;">
                    <div>
                        <div style="font-size:0.72rem; color:#8b95a5; text-transform:uppercase; letter-spacing:0.8px; font-weight:600;">💡 Quanto posso gastar hoje</div>
                        <div style="font-size:2rem; font-weight:900; color:{cor_hoje}; margin:0.2rem 0;">{fmt(valor_hoje)} {emoji_hoje}</div>
                        <div style="font-size:0.72rem; color:#5a6478;">Faltam {dias_restantes} dias · Sobra total: {fmt(rec_mes - desp_mes - simples_mes)}</div>
                    </div>
                    <div style="text-align:right;">
                        <div style="font-size:0.65rem; color:#5a6478;">Fixas pendentes: {fmt(recorrentes_futuras)}</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    # ── Atalhos de Lançamento (Fase 5.3) ──────────────────────────────
    sec("⚡", "Lançamento Rápido")
    atalhos = conn.execute(
        "SELECT a.id, a.descricao, a.valor, a.icone, a.tipo, c.nome, co.nome, a.categoria_id, a.conta_id "
        "FROM atalhos a LEFT JOIN categorias c ON a.categoria_id = c.id "
        "LEFT JOIN contas co ON a.conta_id = co.id"
    ).fetchall()
    
    if atalhos:
        cols_at = st.columns(min(len(atalhos) + 1, 6)) # Máximo 6 colunas
        for i, a in enumerate(atalhos):
            with cols_at[i % 6]:
                if st.button(f"{a[3]}\n{a[1]}", key=f"btn_at_{a[0]}", help=f"{fmt(a[2])} em {a[6]}"):
                    conn.execute(
                        "INSERT INTO transacoes (tipo,descricao,valor,data,categoria_id,conta_id) "
                        "VALUES (?,?,?,?,?,?)",
                        (a[4], a[1], a[2], hoje.strftime("%Y-%m-%d"), a[7], a[8])
                    )
                    conn.commit()
                    st.success(f"Lançamento de {fmt(a[2])} adicionado!")
                    st.rerun()
        
        # Botão para gerenciar
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
        st.info("Crie atalhos para lançar despesas frequentes com um clique.")
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

    # ── Cards de métricas ─────────────────────────────────────────────
    sec("📈", f"Resumo de {MESES_PT[mes_sel]}")
    b_cls = "mv-green" if balanco_mes >= 0 else "mv-red"
    b_bdg = "mb-green" if balanco_mes >= 0 else "mb-red"

    html_cards = f"""
    <div style="display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 1rem;">
        <div style="flex: 1 1 180px; min-width: 160px;">{metric_card("💵","green","Receitas",fmt(rec_mes),"mv-green","Entradas","mb-green")}</div>
        <div style="flex: 1 1 180px; min-width: 160px;">{metric_card("💳","red","Despesas",fmt(desp_mes),"mv-red","Saídas","mb-red")}</div>
        <div style="flex: 1 1 180px; min-width: 160px;">{metric_card("📋","amber","Simples Nacional",fmt(simples_mes),"mv-amber","6% s/ receita","mb-amber")}</div>
        <div style="flex: 1 1 180px; min-width: 160px;">{metric_card("📊","purple","Balanço Líquido",fmt(balanco_mes),b_cls,"Superávit" if balanco_mes>=0 else "Déficit",b_bdg)}</div>
        <div style="flex: 1 1 180px; min-width: 160px;">{metric_card("🏦","blue","Saldo Disponível",fmt(saldo_total),"mv-blue","Livre para uso","mb-blue")}</div>
    </div>
    """
    st.markdown(html_cards, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # ── Score + Regra 50-30-20 ────────────────────────────────────────
    col_sc, col_rule = st.columns(2)

    with col_sc:
        sec("💚", "Saúde Financeira")
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
        sec("📐", "Regra 50-30-20")
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
                values=dpc["total"], hole=0.6,
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
        ml, rv, dv = [], [], []
        for i in range(5, -1, -1):
            p, m2, a2 = get_pref(mes_sel - i, ano_sel)
            ml.append(MESES_PT[m2][:3])
            rv.append(conn.execute(
                "SELECT COALESCE(SUM(valor),0) FROM transacoes WHERE tipo='receita' AND data LIKE ?",
                (f"{p}%",),
            ).fetchone()[0])
            dv.append(conn.execute(
                "SELECT COALESCE(SUM(valor),0) FROM transacoes WHERE tipo='despesa' AND data LIKE ?",
                (f"{p}%",),
            ).fetchone()[0])
        fig_b = go.Figure()
        fig_b.add_trace(go.Bar(x=ml, y=rv, name="Receitas", marker=dict(color="#00d4aa", cornerradius=5)))
        fig_b.add_trace(go.Bar(x=ml, y=dv, name="Despesas", marker=dict(color="#ff4b6e", cornerradius=5)))
        fig_b.update_layout(
            **PLOTLY_LAYOUT, barmode="group", height=340,
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.03)"),
            xaxis=dict(showgrid=False),
        )
        st.plotly_chart(fig_b, key="bar_d")

    # ── Evolução diária ───────────────────────────────────────────────
    sec("📈", "Evolução do Saldo no Mês")
    datas, saldos_dia, acum = [], [], 0
    for d in range(1, dias_mes + 1):
        ds = f"{ano_sel}-{mes_sel:02d}-{d:02d}"
        r = conn.execute(
            "SELECT COALESCE(SUM(valor),0) FROM transacoes WHERE tipo='receita' AND data=?", (ds,),
        ).fetchone()[0]
        de = conn.execute(
            "SELECT COALESCE(SUM(valor),0) FROM transacoes WHERE tipo='despesa' AND data=?", (ds,),
        ).fetchone()[0]
        acum += r - de
        datas.append(d)
        saldos_dia.append(acum)
    fig_l = go.Figure(go.Scatter(
        x=datas, y=saldos_dia, mode="lines+markers",
        line=dict(color="#4e8cff", width=2.5, shape="spline"),
        marker=dict(size=4, color="#4e8cff"),
        fill="tozeroy", fillcolor="rgba(78,140,255,0.08)",
        hovertemplate="Dia %{x}<br>Saldo: R$ %{y:,.2f}<extra></extra>",
    ))
    fig_l.update_layout(
        **PLOTLY_LAYOUT, height=220,
        xaxis=dict(title="Dia", showgrid=False, dtick=5),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.03)",
                   zeroline=True, zerolinecolor="rgba(255,75,110,0.3)"),
    )
    st.plotly_chart(fig_l, key="line_d")

    # ── Top 5 Gastos do Mês (Fase 3.2) ───────────────────────────────
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

    # ── Resumo Anual (Fase 3.1) ───────────────────────────────────────
    with col_annual:
        sec("📅", f"Visão Anual {ano_sel}")
        ml_ano, rv_ano, dv_ano = [], [], []
        total_rec_ano, total_desp_ano = 0, 0
        for m in range(1, 13):
            p = f"{ano_sel}-{m:02d}"
            r_val = conn.execute(
                "SELECT COALESCE(SUM(valor),0) FROM transacoes WHERE tipo='receita' AND data LIKE ?",
                (f"{p}%",),
            ).fetchone()[0]
            d_val = conn.execute(
                "SELECT COALESCE(SUM(valor),0) FROM transacoes WHERE tipo='despesa' AND data LIKE ?",
                (f"{p}%",),
            ).fetchone()[0]
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
            xaxis=dict(showgrid=False),
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
