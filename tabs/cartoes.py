"""
tabs/cartoes.py — Aba de Cartões de Crédito.
Versão 2.5: Cálculo exato de ciclo de fatura, extrato detalhado por fatura e pagamento sem duplicar despesas.
"""
import calendar
import html
import streamlit as st
import pandas as pd
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

from core.utils import fmt, fmt_data_pt
from core.database import saldo_conta, read_sql
from core.models import clear_cache_transacoes
from components.cards import sec, credit_card_visual, ring_progress


# Cores por bandeira/banco
CARD_COLORS = {
    "nubank": ("#8B5CF6", "#6D28D9"),
    "inter": ("#FF6B00", "#CC5500"),
    "itau": ("#003B71", "#002A52"),
    "itaú": ("#003B71", "#002A52"),
    "bradesco": ("#CC092F", "#990720"),
    "bb": ("#FECE00", "#CBA400"),
    "brasil": ("#FECE00", "#CBA400"),
    "caixa": ("#005CA9", "#004680"),
    "c6": ("#1A1A2E", "#0F0F1E"),
    "santander": ("#EC0000", "#990000"),
    "xp": ("#111111", "#2b2b2b"),
    "btg": ("#001E62", "#00123B"),
    "default": ("#a855f7", "#6d28d9"),
}


def _get_card_colors(nome):
    """Detecta cores baseado no nome do cartão."""
    nome_lower = nome.lower()
    for key, colors in CARD_COLORS.items():
        if key in nome_lower:
            return colors
    return CARD_COLORS["default"]


def _calcular_periodo_fatura(ano: int, mes: int, dia_fechamento: int):
    """Calcula com precisão (data_ini, data_fim) do ciclo de fatura mesmo quando dia_fechamento=1 ou 31."""
    dia_f = max(1, min(int(dia_fechamento or 1), 28))
    max_dia_mes = calendar.monthrange(ano, mes)[1]
    dt_fechamento_atual = date(ano, mes, min(dia_f, max_dia_mes))
    dt_fim = dt_fechamento_atual - timedelta(days=1)
    dt_ini = (dt_fechamento_atual - relativedelta(months=1))
    return dt_ini.strftime("%Y-%m-%d"), dt_fim.strftime("%Y-%m-%d")


def render(ctx):
    """Renderiza a aba Cartões de Crédito."""
    conn = ctx["conn"]

    sec("💳", "Seus Cartões de Crédito")
    cartoes = read_sql("SELECT * FROM contas WHERE tipo = 'Cartão de Crédito'", conn)

    if cartoes.empty:
        st.html("""
            <div class="empty-state">
                <div class="empty-icon">💳</div>
                <div class="empty-title">Nenhum cartão cadastrado</div>
                <div class="empty-desc">Vá até a aba 🏦 Contas para adicionar um cartão de crédito e acompanhar suas faturas aqui.</div>
            </div>
        """)
        return

    mes_sel = ctx.get("mes_sel", date.today().month)
    ano_sel = ctx.get("ano_sel", date.today().year)

    for _, c in cartoes.iterrows():
        dia_fecha = c["dia_fechamento"] or 1
        data_ini, data_fim = _calcular_periodo_fatura(ano_sel, mes_sel, dia_fecha)

        desp_fatura = conn.execute(
            "SELECT COALESCE(SUM(valor),0) FROM transacoes WHERE conta_id=? AND tipo='despesa' AND COALESCE(is_transferencia,0)=0 AND data >= ? AND data <= ?",
            (c["id"], data_ini, data_fim)
        ).fetchone()[0]

        rec_fatura = conn.execute(
            "SELECT COALESCE(SUM(valor),0) FROM transacoes WHERE conta_id=? AND tipo='receita' AND data >= ? AND data <= ?",
            (c["id"], data_ini, data_fim)
        ).fetchone()[0]

        fatura_mensal = max(0, desp_fatura - rec_fatura)

        saldo_global = saldo_conta(conn, c["id"])
        fatura_total = -saldo_global if saldo_global < 0 else 0

        limite = c["limite_cartao"] or 0
        limite_disp = max(0, limite - fatura_total)
        pct_uso = min(100, (fatura_total / limite) * 100 if limite > 0 else 0)

        color_from, color_to = _get_card_colors(c["nome"])

        col_visual, col_info = st.columns([1, 2])

        with col_visual:
            st.markdown(
                credit_card_visual(c["nome"], c["icone"], fmt(fatura_mensal), c["dia_vencimento"], color_from, color_to),
                unsafe_allow_html=True,
            )

        with col_info:
            ring_html = ring_progress(
                pct_uso, size=60, stroke=5,
                color="#a855f7" if pct_uso < 70 else ("#f59e0b" if pct_uso < 90 else "#ff4b6e"),
                label=f"{pct_uso:.0f}%",
            )

            st.html(f"""
            <div class="glass-card" style="border-left: 4px solid {color_from};">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;">
                    <div>
                        <div style="font-size:0.68rem;color:var(--text2);text-transform:uppercase;font-weight:600;">Fatura {mes_sel:02d}/{ano_sel}</div>
                        <div style="font-size:1.6rem;font-weight:900;color:{'var(--red)' if fatura_mensal > 0 else 'var(--green)'};">{fmt(fatura_mensal)}</div>
                        <div style="font-size:0.7rem;color:var(--text3);">Vence dia {c['dia_vencimento']} · Ciclo: {fmt_data_pt(data_ini)} a {fmt_data_pt(data_fim)}</div>
                    </div>
                    <div style="text-align:center;">
                        {ring_html}
                        <div style="font-size:0.55rem;color:var(--text3);margin-top:0.2rem;">Limite<br>usado</div>
                    </div>
                </div>
                <div style="display:flex;justify-content:space-between;font-size:0.8rem;margin-bottom:0.4rem;color:var(--text2);">
                    <span>Disponível: <strong style="color:var(--green);">{fmt(limite_disp)}</strong></span>
                    <span>Em aberto total: <strong>{fmt(fatura_total)}</strong> / {fmt(limite)}</span>
                </div>
                <div class="rule-bar-bg" style="height:6px;">
                    <div class="rule-bar-fill" style="width:{pct_uso}%;background:linear-gradient(90deg,{color_from},{color_to});"></div>
                </div>
            </div>
            """)

        # Extrato detalhado e pagamento da fatura lado a lado
        col_ext, col_pag = st.columns(2)
        with col_ext:
            with st.expander(f"📋 Ver Compras da Fatura ({mes_sel:02d}/{ano_sel})"):
                itens_fatura = read_sql(
                    "SELECT t.data, t.descricao, t.valor, t.tipo, c.icone, c.nome as cat "
                    "FROM transacoes t LEFT JOIN categorias c ON t.categoria_id = c.id "
                    "WHERE t.conta_id = ? AND t.data >= ? AND t.data <= ? ORDER BY t.data DESC, t.id DESC",
                    conn, params=(c["id"], data_ini, data_fim),
                )
                if itens_fatura.empty:
                    st.caption("Nenhum lançamento neste ciclo.")
                else:
                    for _, item in itens_fatura.iterrows():
                        ic_it = item["icone"] if pd.notna(item["icone"]) else "💳"
                        cor_it = "#00d4aa" if item["tipo"] == "receita" else "#ff4b6e"
                        sinal_it = "-" if item["tipo"] == "receita" else ""
                        st.html(f"""
                            <div style="display:flex;justify-content:space-between;align-items:center;padding:0.45rem 0;border-bottom:1px solid var(--border);font-size:0.78rem;">
                                <div>
                                    <span style="font-weight:600;color:var(--text);">{ic_it} {html.escape(str(item['descricao']))}</span>
                                    <div style="font-size:0.65rem;color:var(--text3);">{fmt_data_pt(str(item['data']))} · {html.escape(str(item['cat'] or 'Cartão'))}</div>
                                </div>
                                <div style="font-weight:700;color:{cor_it};">{sinal_it}{fmt(item['valor'])}</div>
                            </div>
                        """)

        with col_pag:
            if fatura_mensal > 0:
                with st.expander(f"💳 Pagar Fatura de {mes_sel:02d}/{ano_sel} - {c['nome']}"):
                    with st.form(f"pagar_fatura_{mes_sel}_{c['id']}"):
                        val_pag = st.number_input(
                            "Valor do Pagamento (R$)",
                            min_value=0.01, value=float(fatura_mensal), step=10.0, format="%.2f",
                        )
                        outras_contas = conn.execute(
                            "SELECT id, nome FROM contas WHERE tipo NOT IN ('Cartão de Crédito', 'Reserva de Emergência')"
                        ).fetchall()
                        if outras_contas:
                            conta_pag = st.selectbox("Debitar da conta", outras_contas, format_func=lambda x: x[1])
                        else:
                            st.warning("Nenhuma conta corrente disponível.")
                            conta_pag = None

                        if st.form_submit_button("✅ Confirmar Pagamento", type="primary", use_container_width=True):
                            if conta_pag:
                                data_hoje = date.today().strftime("%Y-%m-%d")
                                # Usa is_transferencia=1 para não duplicar a despesa nas estatísticas do mês
                                conn.execute(
                                    "INSERT INTO transacoes (tipo, descricao, valor, data, conta_id, is_transferencia) VALUES ('despesa', ?, ?, ?, ?, 1)",
                                    (f"Pagamento Fatura {mes_sel:02d}/{ano_sel} - {c['nome']}", val_pag, data_hoje, conta_pag[0]),
                                )
                                conn.execute(
                                    "INSERT INTO transacoes (tipo, descricao, valor, data, conta_id, is_transferencia) VALUES ('receita', ?, ?, ?, ?, 1)",
                                    (f"Pagamento Recebido - Fatura {mes_sel:02d}/{ano_sel}", val_pag, data_hoje, c["id"]),
                                )
                                conn.commit()
                                clear_cache_transacoes()
                                st.toast("✅ Fatura paga com sucesso!")
                                st.rerun()

        st.html("<br>")
