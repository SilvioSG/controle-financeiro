"""
📊 Financeiro — Controle Pessoal
Entrypoint principal do aplicativo Streamlit.
Versão 2.5: Modal rápido global, backup na nuvem/JSON, alíquota configurável, visual fintech.
"""
import streamlit as st
import calendar
from datetime import date
import sys
import asyncio

# Fix para erro no Windows: ConnectionResetError [WinError 10054] do Tornado/Streamlit
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from core.database import get_connection, init_db, seed_categorias, seed_conta_padrao
from core.utils import fmt, MESES_PT, get_taxa_simples, processar_tags
from core.models import get_contas, get_categorias, clear_cache_transacoes
from components.styles import inject_css
from intelligence.score import calcular_score
from intelligence.categorizer import sugerir_categoria, aprender_categoria
from core.auth import check_password, logout

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
if conn.is_postgres:
    if not check_password():
        st.stop()
else:
    st.session_state["authenticated"] = True


# ─── Modal Global de Nova Transação ──────────────────────────────────────────
@st.dialog("➕ Lançamento Rápido")
def modal_nova_transacao():
    contas_df = get_contas(conn)
    categorias_df = get_categorias(conn)

    c1, c2 = st.columns(2)
    with c1:
        tipo_tx = st.selectbox(
            "Tipo", ["despesa", "receita"],
            format_func=lambda x: "🔴 Despesa" if x == "despesa" else "🟢 Receita",
            key="modal_tipo_tx",
        )
    with c2:
        data_tx = st.date_input("Data", value=date.today(), key="modal_data_tx")

    desc_tx = st.text_input("Descrição", placeholder="Ex: iFood, Supermercado, Salário...", key="modal_desc_tx")
    valor_tx = st.number_input("Valor (R$)", min_value=0.01, step=10.0, format="%.2f", key="modal_val_tx")

    c3, c4 = st.columns(2)
    with c3:
        if not categorias_df.empty:
            cats_filtradas = categorias_df[categorias_df["tipo"].isin([tipo_tx, "ambos"])]
            if cats_filtradas.empty:
                cats_filtradas = categorias_df
            co = {f"{r['icone']} {r['nome']}": r["id"] for _, r in cats_filtradas.iterrows()}
            co_keys = list(co.keys())
            default_idx = 0
            if desc_tx.strip():
                sug_id, _ = sugerir_categoria(conn, desc_tx)
                if sug_id:
                    for i, (_, v) in enumerate(co.items()):
                        if v == sug_id:
                            default_idx = i
                            break
            cs = st.selectbox("Categoria (auto-sugerida)", co_keys, index=default_idx, key="modal_cat_tx")
            cat_id = co[cs]
        else:
            cat_id = None
    with c4:
        if not contas_df.empty:
            co2 = {f"{r['icone']} {r['nome']}": r["id"] for _, r in contas_df.iterrows()}
            cs2 = st.selectbox("Conta", list(co2.keys()), key="modal_conta_tx")
            conta_id = co2[cs2]
        else:
            conta_id = None

    tags_tx = st.text_input("Tags (opcional, separadas por vírgula)", placeholder="Ex: urgente, trabalho", key="modal_tags_tx")
    recorrente_tx = st.checkbox("🔄 Conta Fixa Mensal (Recorrente)", key="modal_rec_tx")

    if st.button("💾 Salvar Lançamento", type="primary", use_container_width=True):
        if desc_tx.strip() and valor_tx > 0 and cat_id and conta_id:
            if getattr(conn, 'is_postgres', False):
                cur = conn.execute(
                    "INSERT INTO transacoes (tipo,descricao,valor,data,categoria_id,conta_id,recorrente,observacao) "
                    "VALUES (?,?,?,?,?,?,?,?) RETURNING id",
                    (tipo_tx, desc_tx.strip(), valor_tx, data_tx.strftime("%Y-%m-%d"), cat_id, conta_id, 1 if recorrente_tx else 0, ""),
                )
                tx_id = cur.fetchone()[0]
            else:
                cur = conn.execute(
                    "INSERT INTO transacoes (tipo,descricao,valor,data,categoria_id,conta_id,recorrente,observacao) "
                    "VALUES (?,?,?,?,?,?,?,?)",
                    (tipo_tx, desc_tx.strip(), valor_tx, data_tx.strftime("%Y-%m-%d"), cat_id, conta_id, 1 if recorrente_tx else 0, ""),
                )
                tx_id = cur.lastrowid

            if tags_tx.strip():
                processar_tags(conn, tx_id, tags_tx)
            aprender_categoria(conn, desc_tx, cat_id)
            conn.commit()
            clear_cache_transacoes()
            st.toast("✅ Lançamento registrado com sucesso!")
            st.rerun()
        else:
            st.error("Preencha descrição e valor maior que zero.")


# ─── Defaults (caso sidebar falhe) ────────────────────────────────────────────
hoje = date.today()
mes_sel = hoje.month
ano_sel = hoje.year
prefixo_mes = f"{ano_sel}-{mes_sel:02d}"
dias_mes = calendar.monthrange(ano_sel, mes_sel)[1]
taxa_simples_atual = get_taxa_simples()

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    try:
        st.markdown(
            '<div class="sidebar-brand"><h2>📊 <span>Financeiro</span></h2><p>Controle Pessoal Pro</p></div>',
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

        # Auto-sync da Meta de Reserva apenas se não estiver vinculada a conta específica
        if saldo_reserva > 0:
            conn.execute("""
                UPDATE metas 
                SET valor_atual = ? 
                WHERE conta_id IS NULL AND (LOWER(nome) LIKE ? OR LOWER(nome) LIKE ?)
            """, (saldo_reserva, '%reserva%', '%emergência%'))
            conn.commit()

        # Garantir que apenas o botão "Usar Reserva" (observacao = 'Gerado por: Usar Reserva')
        # seja tratado como movimentação patrimonial (is_transferencia = 1),
        # mantendo salários e lançamentos normais na conta Nubank como receita/despesa do mês
        if "reserva_tx_fixed_v2" not in st.session_state:
            conn.execute("""
                UPDATE transacoes
                SET is_transferencia = 1
                WHERE observacao = 'Gerado por: Usar Reserva' AND COALESCE(is_transferencia, 0) = 0
            """)
            conn.execute("""
                UPDATE transacoes
                SET is_transferencia = 0
                WHERE is_transferencia = 1
                  AND COALESCE(observacao, '') != 'Gerado por: Usar Reserva'
                  AND descricao NOT LIKE 'Transferência%'
                  AND descricao NOT LIKE 'Pagamento Fatura%'
                  AND descricao NOT LIKE 'Pagamento Recebido - Fatura%'
            """)
            clear_cache_transacoes()
            st.session_state["reserva_tx_fixed_v2"] = True

        rec_mes = conn.execute(
            "SELECT COALESCE(SUM(valor),0) FROM transacoes WHERE tipo='receita' AND COALESCE(is_transferencia,0)=0 AND data LIKE ?",
            (f"{prefixo_mes}%",),
        ).fetchone()[0]
        desp_mes = conn.execute(
            "SELECT COALESCE(SUM(valor),0) FROM transacoes WHERE tipo='despesa' AND COALESCE(is_transferencia,0)=0 AND data LIKE ?",
            (f"{prefixo_mes}%",),
        ).fetchone()[0]

        taxa_simples_atual = get_taxa_simples()
        simples_mes = rec_mes * taxa_simples_atual
        balanco_mes = rec_mes - desp_mes - simples_mes

        cor_balanco = "#00d4aa" if balanco_mes >= 0 else "#ff4b6e"
        label_imposto = f"📋 Imposto ({taxa_simples_atual*100:.1f}%)" if taxa_simples_atual > 0 else "📋 Imposto (Isento)"
        st.html(f"""
            <div class="sidebar-stat"><span class="ss-label">💰 Saldo do Mês</span><span class="ss-value" style="color:{cor_balanco}">{fmt(balanco_mes)}</span></div>
            <div class="sidebar-stat"><span class="ss-label">🛡️ Reserva</span><span class="ss-value" style="color:#4e8cff">{fmt(saldo_reserva)}</span></div>
            <div class="sidebar-stat"><span class="ss-label">📈 Receitas</span><span class="ss-value" style="color:#00d4aa">{fmt(rec_mes)}</span></div>
            <div class="sidebar-stat"><span class="ss-label">📉 Despesas</span><span class="ss-value" style="color:#ff4b6e">{fmt(desp_mes)}</span></div>
            <div class="sidebar-stat"><span class="ss-label">{label_imposto}</span><span class="ss-value" style="color:#f59e0b">{fmt(simples_mes)}</span></div>
        """)
        st.markdown("---")

        # Score rápido na sidebar
        score = calcular_score(conn, rec_mes, desp_mes, simples_mes, prefixo_mes, mes_sel, ano_sel, saldo_reserva)
        score_cor = "#00d4aa" if score >= 70 else ("#f59e0b" if score >= 40 else "#ff4b6e")
        score_label = "Excelente" if score >= 80 else ("Bom" if score >= 60 else ("Regular" if score >= 40 else "Crítico"))

        from components.cards import ring_progress
        ring_html = ring_progress(score, size=55, stroke=5, color=score_cor, label=str(score))

        st.html(f"""
            <div class="sidebar-stat" style="flex-direction:column;align-items:center;padding:0.8rem;">
                <span class="ss-label" style="margin-bottom:0.3rem;">💚 Saúde Financeira</span>
                <div style="display:flex;align-items:center;gap:0.6rem;">
                    {ring_html}
                    <span class="ss-value" style="color:{score_cor};font-size:0.8rem;">{score_label}</span>
                </div>
            </div>
        """)
        st.caption(f"📅 Competência: {MESES_PT[mes_sel]} / {ano_sel}")

        st.markdown("---")
        if st.button("📄 Gerar Relatório (PDF)", use_container_width=True):
            from intelligence.report import gerar_relatorio_pdf
            path_pdf = gerar_relatorio_pdf(conn, mes_sel, ano_sel, prefixo_mes, rec_mes, desp_mes, simples_mes, balanco_mes, score)
            with open(path_pdf, "rb") as pdf_file:
                st.download_button(
                    label="📥 Baixar Relatório Executivo",
                    data=pdf_file,
                    file_name=f"Relatorio_Financeiro_{prefixo_mes}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    type="primary",
                )

        # ── Configurações & Backup ────────────────────────────────────
        with st.expander("⚙️ Configurações & Backup"):
            st.caption("Ajuste a alíquota de imposto (0% para PF, 6% para Simples Nacional):")
            nova_taxa = st.number_input(
                "Alíquota Imposto (%)",
                min_value=0.0,
                max_value=35.0,
                value=float(taxa_simples_atual * 100),
                step=0.5,
                format="%.1f",
                key="input_taxa_simples",
            )
            if abs(nova_taxa - (taxa_simples_atual * 100)) > 0.01:
                st.session_state["taxa_simples_pct"] = nova_taxa
                st.rerun()

            if conn.is_postgres:
                if st.button("📦 Gerar Backup Completo (JSON)", use_container_width=True):
                    try:
                        from core.backup import exportar_json
                        st.session_state["backup_json_bytes"] = exportar_json(conn)
                    except Exception as e_bak:
                        st.caption(f"Backup indisponível: {e_bak}")
                if "backup_json_bytes" in st.session_state:
                    st.download_button(
                        label="💾 Baixar Backup (JSON)",
                        data=st.session_state["backup_json_bytes"],
                        file_name=f"backup_financeiro_{hoje.strftime('%Y%m%d')}.json",
                        mime="application/json",
                        use_container_width=True,
                        type="primary",
                    )

        # ── Glossário Financeiro ──────────────────────────────────────
        with st.expander("📖 Glossário Financeiro"):
            from components.glossario import render_glossario
            render_glossario()

        if st.session_state.get("user_email"):
            st.markdown("---")
            st.caption(f"👤 {st.session_state['user_email']}")
            if st.button("🚪 Sair da Conta", use_container_width=True):
                logout()

    except Exception as e:
        import traceback
        st.error(f"❌ Erro na sidebar: {e}")
        st.code(traceback.format_exc())

# ─── Header com Botão de Ação Rápida ─────────────────────────────────────────
col_hdr, col_quick = st.columns([5, 1.3], vertical_alignment="center")
with col_hdr:
    st.markdown(
        f'<div class="app-header" style="margin-bottom:0.5rem;"><h1>📊 <span>Controle Financeiro Pessoal</span></h1>'
        f'<p>Organize suas finanças com inteligência · {MESES_PT[mes_sel]} {ano_sel}</p></div>',
        unsafe_allow_html=True,
    )
with col_quick:
    if st.button("➕ Novo Lançamento", type="primary", use_container_width=True, help="Registrar receita ou despesa rapidamente"):
        modal_nova_transacao()

# ─── Contexto compartilhado entre abas ────────────────────────────────────────
ctx = {
    "conn": conn,
    "prefixo_mes": prefixo_mes,
    "mes_sel": mes_sel,
    "ano_sel": ano_sel,
    "rec_mes": rec_mes,
    "desp_mes": desp_mes,
    "simples_mes": simples_mes,
    "taxa_simples": taxa_simples_atual,
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

if total_txs < 3:
    step_1_done = total_contas > 1
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

    st.html(f"""
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
    """)

# ─── Abas (Lazy Loading) ───────────────────────────────────────────────────────
opcoes_abas = {
    "🏠 Dashboard": "dashboard",
    "💰 Transações": "transacoes",
    "📊 Orçamento": "orcamento",
    "💳 Cartões": "cartoes",
    "🏦 Contas": "contas",
    "🛡️ Metas": "metas",
    "💹 Investimentos": "investimentos",
    "💡 Insights": "insights",
    "📁 Categorias": "categorias",
}

if "aba_ativa" not in st.session_state:
    st.session_state["aba_ativa"] = list(opcoes_abas.keys())[0]

aba_selecionada = st.pills(
    "Navegação",
    options=list(opcoes_abas.keys()),
    default=st.session_state["aba_ativa"],
    label_visibility="collapsed",
)

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

aba_slug = opcoes_abas[aba_selecionada]
if aba_slug == "dashboard":
    render_dashboard(ctx)
elif aba_slug == "insights":
    render_insights(ctx)
elif aba_slug == "transacoes":
    render_transacoes(ctx)
elif aba_slug == "orcamento":
    render_orcamento(ctx)
elif aba_slug == "investimentos":
    render_investimentos(ctx)
elif aba_slug == "cartoes":
    render_cartoes(ctx)
elif aba_slug == "contas":
    render_contas(ctx)
elif aba_slug == "categorias":
    render_categorias(ctx)
elif aba_slug == "metas":
    render_metas(ctx)
