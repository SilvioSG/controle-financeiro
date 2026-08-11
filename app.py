"""
📊 Financeiro — Controle Pessoal
Entrypoint principal do aplicativo Streamlit.
"""
import streamlit as st
import calendar
from datetime import date

from core.database import get_connection, init_db, seed_categorias, seed_conta_padrao, saldo_conta
from core.utils import fmt, MESES_PT, TAXA_SIMPLES
from components.styles import inject_css
from intelligence.score import calcular_score
from core.auth import check_password

# ─── Configuração ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Financeiro — Controle Pessoal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


inject_css()

# ─── Autenticação ────────────────────────────────────────────────────────────
if not check_password():
    st.stop()

# ─── Banco de Dados ──────────────────────────────────────────────────────────
conn = get_connection()
init_db(conn)
seed_categorias(conn)
seed_conta_padrao(conn)

# ─── Defaults (caso sidebar falhe) ────────────────────────────────────────────
hoje = date.today()
mes_sel = hoje.month
ano_sel = hoje.year
prefixo_mes = f"{ano_sel}-{mes_sel:02d}"
dias_mes = calendar.monthrange(ano_sel, mes_sel)[1]

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    try:
        st.markdown(
            '<div class="sidebar-brand"><h2>📊 <span>Financeiro</span></h2><p>Controle Pessoal</p></div>',
            unsafe_allow_html=True,
        )
        st.markdown("---")

        hoje = date.today()
        col_m, col_a = st.columns(2)
        with col_m:
            mes_sel = st.selectbox("Mês", range(1, 13), index=hoje.month - 1, format_func=lambda x: MESES_PT[x])
        with col_a:
            ano_sel = st.selectbox("Ano", range(2020, 2031), index=hoje.year - 2020)
        st.markdown("---")

        prefixo_mes = f"{ano_sel}-{mes_sel:02d}"
        dias_mes = calendar.monthrange(ano_sel, mes_sel)[1]

        # Saldo das contas normais (livre para gasto)
        saldo_total = sum(
            saldo_conta(conn, r[0])
            for r in conn.execute(
                "SELECT id FROM contas WHERE tipo NOT IN ('Reserva de Emergência', 'Cartão de Crédito')"
            ).fetchall()
        )

        # Saldo de todas as reservas
        saldo_reserva = sum(
            saldo_conta(conn, r[0])
            for r in conn.execute("SELECT id FROM contas WHERE tipo = 'Reserva de Emergência'").fetchall()
        )

        rec_total_todas = conn.execute(
            "SELECT COALESCE(SUM(valor),0) FROM transacoes WHERE tipo='receita'"
        ).fetchone()[0]
        saldo_total -= rec_total_todas * TAXA_SIMPLES

        rec_mes = conn.execute(
            "SELECT COALESCE(SUM(valor),0) FROM transacoes WHERE tipo='receita' AND data LIKE ?",
            (f"{prefixo_mes}%",),
        ).fetchone()[0]
        desp_mes = conn.execute(
            "SELECT COALESCE(SUM(valor),0) FROM transacoes WHERE tipo='despesa' AND data LIKE ?",
            (f"{prefixo_mes}%",),
        ).fetchone()[0]
        simples_mes = rec_mes * TAXA_SIMPLES
        balanco_mes = rec_mes - desp_mes - simples_mes

        cor_saldo = "#00d4aa" if saldo_total >= 0 else "#ff4b6e"
        st.markdown(f"""
            <div class="sidebar-stat"><span class="ss-label">🏦 Saldo Disponível</span><span class="ss-value" style="color:{cor_saldo}">{fmt(saldo_total)}</span></div>
            <div class="sidebar-stat"><span class="ss-label">🛡️ Reserva</span><span class="ss-value" style="color:#4e8cff">{fmt(saldo_reserva)}</span></div>
            <div class="sidebar-stat"><span class="ss-label">📈 Receitas</span><span class="ss-value" style="color:#00d4aa">{fmt(rec_mes)}</span></div>
            <div class="sidebar-stat"><span class="ss-label">📉 Despesas</span><span class="ss-value" style="color:#ff4b6e">{fmt(desp_mes)}</span></div>
            <div class="sidebar-stat"><span class="ss-label">📋 Simples (6%)</span><span class="ss-value" style="color:#f59e0b">{fmt(simples_mes)}</span></div>
        """, unsafe_allow_html=True)
        st.markdown("---")

        # Score rápido na sidebar
        score = calcular_score(conn, rec_mes, desp_mes, simples_mes, prefixo_mes, mes_sel, ano_sel)
        score_cor = "#00d4aa" if score >= 70 else ("#f59e0b" if score >= 40 else "#ff4b6e")
        score_label = "Excelente" if score >= 80 else ("Bom" if score >= 60 else ("Regular" if score >= 40 else "Crítico"))
        st.markdown(f"""
            <div class="sidebar-stat">
                <span class="ss-label">💚 Saúde Financeira</span>
                <span class="ss-value" style="color:{score_cor}">{score}/100 · {score_label}</span>
            </div>
        """, unsafe_allow_html=True)
        st.caption(f"📅 {MESES_PT[mes_sel]} / {ano_sel}")

        st.markdown("---")
        if st.button("📄 Gerar Relatório (PDF)", width='stretch'):
            from intelligence.report import gerar_relatorio_pdf
            path_pdf = gerar_relatorio_pdf(conn, mes_sel, ano_sel, prefixo_mes, rec_mes, desp_mes, simples_mes, balanco_mes, score)
            with open(path_pdf, "rb") as pdf_file:
                st.download_button(
                    label="📥 Baixar PDF",
                    data=pdf_file,
                    file_name=f"Relatorio_Financeiro_{prefixo_mes}.pdf",
                    mime="application/pdf",
                    width='stretch',
                    type="primary"
                )
    except Exception as e:
        import traceback
        st.error(f"❌ Erro na sidebar: {e}")
        st.code(traceback.format_exc())

# ─── Header ──────────────────────────────────────────────────────────────────
st.markdown(
    f'<div class="app-header"><h1>📊 <span>Controle Financeiro Pessoal</span></h1>'
    f'<p>Organize suas finanças · {MESES_PT[mes_sel]} {ano_sel}</p></div>',
    unsafe_allow_html=True,
)

# ─── Contexto compartilhado entre abas ────────────────────────────────────────
ctx = {
    "conn": conn,
    "prefixo_mes": prefixo_mes,
    "mes_sel": mes_sel,
    "ano_sel": ano_sel,
    "rec_mes": rec_mes,
    "desp_mes": desp_mes,
    "simples_mes": simples_mes,
    "balanco_mes": balanco_mes,
    "saldo_total": saldo_total,
    "saldo_reserva": saldo_reserva,
    "score": score,
    "score_cor": score_cor,
    "score_label": score_label,
    "hoje": hoje,
    "dias_mes": dias_mes,
}

# ─── Onboarding (Fase 5.2) ───────────────────────────────────────────────────
total_txs = conn.execute("SELECT COUNT(id) FROM transacoes").fetchone()[0]
if total_txs == 0:
    st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(78,140,255,0.1), rgba(0,212,170,0.1)); padding: 2rem; border-radius: 12px; border-left: 5px solid #00d4aa; margin-bottom: 1.5rem;">
            <h2>👋 Bem-vindo ao Financeiro!</h2>
            <p style="font-size: 1.1rem; color: #f0f2f5;">Parece que este é o seu primeiro acesso. Seu banco de dados foi inicializado com sucesso!</p>
            <p style="color: #8b95a5;">Para começar, acesse a aba <b>Transações</b> e registre seu primeiro ganho ou gasto. O painel ganhará vida assim que você adicionar alguns dados.</p>
        </div>
    """, unsafe_allow_html=True)

# ─── Abas ────────────────────────────────────────────────────────────────────
tab_dash, tab_insights, tab_trans, tab_orc, tab_invest, tab_cartoes, tab_contas, tab_cats, tab_metas = st.tabs(
    ["🏠 Dashboard", "💡 Insights", "💰 Transações", "📊 Orçamento",
     "💹 Investimentos", "💳 Cartões", "🏦 Contas", "📁 Categorias", "🛡️ Metas"]
)

from tabs.dashboard import render as render_dashboard
from tabs.insights import render as render_insights
from tabs.transacoes import render as render_transacoes
from tabs.orcamento import render as render_orcamento
from tabs.investimentos import render as render_investimentos
from tabs.cartoes import render as render_cartoes
from tabs.contas import render as render_contas
from tabs.categorias import render as render_categorias
from tabs.metas import render as render_metas

with tab_dash:
    render_dashboard(ctx)

with tab_insights:
    render_insights(ctx)

with tab_trans:
    render_transacoes(ctx)

with tab_orc:
    render_orcamento(ctx)

with tab_invest:
    render_investimentos(ctx)

with tab_cartoes:
    render_cartoes(ctx)

with tab_contas:
    render_contas(ctx)

with tab_cats:
    render_categorias(ctx)

with tab_metas:
    render_metas(ctx)