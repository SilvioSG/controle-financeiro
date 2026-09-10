"""
📊 Financeiro — Controle Pessoal
Entrypoint principal do aplicativo Streamlit.
Versão 2.0: Onboarding guiado, glossário na sidebar, visual premium.
"""
import streamlit as st
import calendar
from datetime import date
import sys
import asyncio

# Fix para erro no Windows: ConnectionResetError [WinError 10054] do Tornado/Streamlit
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

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

# ─── Banco de Dados ──────────────────────────────────────────────────────────
conn = get_connection()
init_db(conn)

if "db_initialized" not in st.session_state:
    seed_categorias(conn)
    seed_conta_padrao(conn)
    st.session_state["db_initialized"] = True

# ─── Autenticação ────────────────────────────────────────────────────────────
# Se o Supabase está fora do ar (fallback para SQLite), pular autenticação
if conn.is_postgres:
    if not check_password():
        st.stop()
else:
    # SQLite local: app funciona sem autenticação
    st.session_state["authenticated"] = True

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
            ano_sel = st.selectbox("Ano", range(2020, hoje.year + 5), index=hoje.year - 2020)
        st.markdown("---")

        prefixo_mes = f"{ano_sel}-{mes_sel:02d}"
        dias_mes = calendar.monthrange(ano_sel, mes_sel)[1]

        # Saldo de todas as reservas
        saldo_reserva = conn.execute("""
            SELECT COALESCE(SUM(
                COALESCE(c.saldo_inicial, 0) +
                COALESCE((SELECT SUM(valor) FROM transacoes WHERE conta_id = c.id AND tipo='receita'), 0) -
                COALESCE((SELECT SUM(valor) FROM transacoes WHERE conta_id = c.id AND tipo='despesa'), 0)
            ), 0) FROM contas c WHERE c.tipo = 'Reserva de Emergência'
        """).fetchone()[0]

        rec_mes = conn.execute(
            "SELECT COALESCE(SUM(valor),0) FROM transacoes WHERE tipo='receita' AND COALESCE(is_transferencia,0)=0 AND data LIKE ?",
            (f"{prefixo_mes}%",),
        ).fetchone()[0]
        desp_mes = conn.execute(
            "SELECT COALESCE(SUM(valor),0) FROM transacoes WHERE tipo='despesa' AND COALESCE(is_transferencia,0)=0 AND data LIKE ?",
            (f"{prefixo_mes}%",),
        ).fetchone()[0]
        simples_mes = rec_mes * TAXA_SIMPLES
        balanco_mes = rec_mes - desp_mes - simples_mes

        cor_balanco = "#00d4aa" if balanco_mes >= 0 else "#ff4b6e"
        st.markdown(f"""
            <div class="sidebar-stat"><span class="ss-label">💰 Saldo do Mês</span><span class="ss-value" style="color:{cor_balanco}">{fmt(balanco_mes)}</span></div>
            <div class="sidebar-stat"><span class="ss-label">🛡️ Reserva</span><span class="ss-value" style="color:#4e8cff">{fmt(saldo_reserva)}</span></div>
            <div class="sidebar-stat"><span class="ss-label">📈 Receitas</span><span class="ss-value" style="color:#00d4aa">{fmt(rec_mes)}</span></div>
            <div class="sidebar-stat"><span class="ss-label">📉 Despesas</span><span class="ss-value" style="color:#ff4b6e">{fmt(desp_mes)}</span></div>
            <div class="sidebar-stat"><span class="ss-label">📋 Simples (6%)</span><span class="ss-value" style="color:#f59e0b">{fmt(simples_mes)}</span></div>
        """, unsafe_allow_html=True)
        st.markdown("---")

        # Score rápido na sidebar
        score = calcular_score(conn, rec_mes, desp_mes, simples_mes, prefixo_mes, mes_sel, ano_sel, saldo_reserva)
        score_cor = "#00d4aa" if score >= 70 else ("#f59e0b" if score >= 40 else "#ff4b6e")
        score_label = "Excelente" if score >= 80 else ("Bom" if score >= 60 else ("Regular" if score >= 40 else "Crítico"))
        
        # Score como mini-gauge visual
        from components.cards import ring_progress
        ring_html = ring_progress(score, size=55, stroke=5, color=score_cor, label=str(score))
        
        st.markdown(f"""
            <div class="sidebar-stat" style="flex-direction:column;align-items:center;padding:0.8rem;">
                <span class="ss-label" style="margin-bottom:0.3rem;">💚 Saúde Financeira</span>
                <div style="display:flex;align-items:center;gap:0.6rem;">
                    {ring_html}
                    <span class="ss-value" style="color:{score_cor};font-size:0.8rem;">{score_label}</span>
                </div>
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
        
        # ── Glossário Financeiro ──────────────────────────────────────
        st.markdown("---")
        with st.expander("📖 Glossário Financeiro"):
            from components.glossario import render_glossario
            render_glossario()
            
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
    "saldo_total": balanco_mes,
    "saldo_reserva": saldo_reserva,
    "score": score,
    "score_cor": score_cor,
    "score_label": score_label,
    "hoje": hoje,
    "dias_mes": dias_mes,
}

# ─── Onboarding (v2.0 — Wizard Guiado) ───────────────────────────────────────
total_txs = conn.execute("SELECT COUNT(id) FROM transacoes").fetchone()[0]
total_contas = conn.execute("SELECT COUNT(id) FROM contas").fetchone()[0]
total_metas = conn.execute("SELECT COUNT(id) FROM metas").fetchone()[0]
total_orc = conn.execute("SELECT COUNT(id) FROM orcamentos").fetchone()[0]

# Mostrar onboarding se poucos dados
if total_txs < 3:
    steps_done = 0
    step_1_done = total_contas > 1  # Pelo menos criou uma conta além da padrão
    step_2_done = total_txs > 0
    step_3_done = total_orc > 0
    step_4_done = total_metas > 0
    steps_done = sum([step_1_done, step_2_done, step_3_done, step_4_done])
    pct_done = (steps_done / 4) * 100
    
    s1_cls = "done" if step_1_done else "pending"
    s2_cls = "done" if step_2_done else "pending"
    s3_cls = "done" if step_3_done else "pending"
    s4_cls = "done" if step_4_done else "pending"
    
    s1_icon = "✓" if step_1_done else "1"
    s2_icon = "✓" if step_2_done else "2"
    s3_icon = "✓" if step_3_done else "3"
    s4_icon = "✓" if step_4_done else "4"
    
    st.markdown(f"""
        <div class="onboarding-card">
            <h2 style="margin:0 0 0.3rem 0;font-size:1.3rem;color:var(--text);">👋 Bem-vindo ao Financeiro!</h2>
            <p style="font-size:0.85rem;color:var(--text2);margin:0 0 1.2rem 0;">
                Configure seu app em 4 passos rápidos. Seu banco de dados já foi inicializado! 🎉
            </p>
            
            <div class="onboarding-step">
                <div class="step-number {s1_cls}">{s1_icon}</div>
                <div>
                    <div class="step-title">{"✅ " if step_1_done else ""}Crie suas contas</div>
                    <div class="step-desc">Adicione suas contas bancárias na aba 🏦 Contas</div>
                </div>
            </div>
            <div class="onboarding-step">
                <div class="step-number {s2_cls}">{s2_icon}</div>
                <div>
                    <div class="step-title">{"✅ " if step_2_done else ""}Registre uma transação</div>
                    <div class="step-desc">Lance sua primeira receita ou despesa na aba 💰 Transações</div>
                </div>
            </div>
            <div class="onboarding-step">
                <div class="step-number {s3_cls}">{s3_icon}</div>
                <div>
                    <div class="step-title">{"✅ " if step_3_done else ""}Defina um orçamento</div>
                    <div class="step-desc">Crie limites de gasto por categoria na aba 📊 Orçamento</div>
                </div>
            </div>
            <div class="onboarding-step">
                <div class="step-number {s4_cls}">{s4_icon}</div>
                <div>
                    <div class="step-title">{"✅ " if step_4_done else ""}Crie sua primeira meta</div>
                    <div class="step-desc">Defina um objetivo financeiro na aba 🛡️ Metas</div>
                </div>
            </div>
            
            <div class="onboarding-progress">
                <div class="onboarding-progress-fill" style="width:{pct_done}%;"></div>
            </div>
            <div style="text-align:center;margin-top:0.5rem;font-size:0.72rem;color:var(--text2);">{steps_done}/4 passos concluídos</div>
        </div>
    """, unsafe_allow_html=True)

# ─── Abas (Lazy Loading) ───────────────────────────────────────────────────────
opcoes_abas = {
    "🏠 Dashboard": "dashboard",
    "💡 Insights": "insights",
    "💰 Transações": "transacoes",
    "📊 Orçamento": "orcamento",
    "💹 Investimentos": "investimentos",
    "💳 Cartões": "cartoes",
    "🏦 Contas": "contas",
    "📁 Categorias": "categorias",
    "🛡️ Metas": "metas"
}

if "aba_ativa" not in st.session_state:
    st.session_state["aba_ativa"] = list(opcoes_abas.keys())[0]

# O st.pills permite seleção igual a abas
aba_selecionada = st.pills(
    "Navegação", 
    options=list(opcoes_abas.keys()),
    default=st.session_state["aba_ativa"],
    label_visibility="collapsed"
)

# Se o usuário desselecionar (clicar no pill já ativo), o Streamlit retorna None.
# Precisamos manter a seleção anterior.
if aba_selecionada is None:
    aba_selecionada = st.session_state["aba_ativa"]
else:
    st.session_state["aba_ativa"] = aba_selecionada

st.markdown("---")

from tabs.dashboard import render as render_dashboard
from tabs.insights import render as render_insights
from tabs.transacoes import render as render_transacoes
from tabs.orcamento import render as render_orcamento
from tabs.investimentos import render as render_investimentos
from tabs.cartoes import render as render_cartoes
from tabs.contas import render as render_contas
from tabs.categorias import render as render_categorias
from tabs.metas import render as render_metas

if opcoes_abas[aba_selecionada] == "dashboard":
    render_dashboard(ctx)
elif opcoes_abas[aba_selecionada] == "insights":
    render_insights(ctx)
elif opcoes_abas[aba_selecionada] == "transacoes":
    render_transacoes(ctx)
elif opcoes_abas[aba_selecionada] == "orcamento":
    render_orcamento(ctx)
elif opcoes_abas[aba_selecionada] == "investimentos":
    render_investimentos(ctx)
elif opcoes_abas[aba_selecionada] == "cartoes":
    render_cartoes(ctx)
elif opcoes_abas[aba_selecionada] == "contas":
    render_contas(ctx)
elif opcoes_abas[aba_selecionada] == "categorias":
    render_categorias(ctx)
elif opcoes_abas[aba_selecionada] == "metas":
    render_metas(ctx)