"""
tabs/cartoes.py — Aba de Cartões de Crédito.
Versão 2.0: Visual 3D de cartão, detalhamento de fatura melhorado.
"""
import streamlit as st
import pandas as pd
from datetime import date

from core.utils import fmt
from core.database import saldo_conta, read_sql
from components.cards import sec, credit_card_visual, ring_progress


# Cores por bandeira/banco
CARD_COLORS = {
    "nubank": ("#8B5CF6", "#6D28D9"),
    "inter": ("#FF6B00", "#CC5500"),
    "itau": ("#003B71", "#002A52"),
    "bradesco": ("#CC092F", "#990720"),
    "bb": ("#FECE00", "#CBA400"),
    "caixa": ("#005CA9", "#004680"),
    "c6": ("#1A1A2E", "#0F0F1E"),
    "default": ("#a855f7", "#6d28d9"),
}

def _get_card_colors(nome):
    """Detecta cores baseado no nome do cartão."""
    nome_lower = nome.lower()
    for key, colors in CARD_COLORS.items():
        if key in nome_lower:
            return colors
    return CARD_COLORS["default"]


def render(ctx):
    """Renderiza a aba Cartões de Crédito."""
    conn = ctx["conn"]

    sec("💳", "Seus Cartões de Crédito")
    cartoes = read_sql("SELECT * FROM contas WHERE tipo = 'Cartão de Crédito'", conn)

    if cartoes.empty:
        st.markdown("""
            <div class="empty-state">
                <div class="empty-icon">💳</div>
                <div class="empty-title">Nenhum cartão cadastrado</div>
                <div class="empty-desc">Vá até a aba 🏦 Contas para adicionar um cartão de crédito e acompanhar suas faturas aqui.</div>
            </div>
        """, unsafe_allow_html=True)
        return

    mes_sel = ctx.get("mes_sel", date.today().month)
    ano_sel = ctx.get("ano_sel", date.today().year)

    for _, c in cartoes.iterrows():
        dia_fecha = c["dia_fechamento"] or 1
        
        mes_ant = mes_sel - 1 if mes_sel > 1 else 12
        ano_ant = ano_sel if mes_sel > 1 else ano_sel - 1
        
        data_ini = f"{ano_ant}-{mes_ant:02d}-{dia_fecha:02d}"
        data_fim = f"{ano_sel}-{mes_sel:02d}-{dia_fecha-1:02d}"
        
        desp_fatura = conn.execute(
            "SELECT COALESCE(SUM(valor),0) FROM transacoes WHERE conta_id=? AND tipo='despesa' AND data >= ? AND data <= ?",
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
        limite_disp = limite - fatura_total
        pct_uso = min(100, (fatura_total / limite) * 100 if limite > 0 else 0)
        
        color_from, color_to = _get_card_colors(c["nome"])
        
        col_visual, col_info = st.columns([1, 2])
        
        with col_visual:
            st.markdown(
                credit_card_visual(c["nome"], c["icone"], fmt(fatura_mensal), c["dia_vencimento"], color_from, color_to),
                unsafe_allow_html=True
            )
        
        with col_info:
            # Ring progress de uso do limite
            ring_html = ring_progress(pct_uso, size=60, stroke=5, 
                                       color="#a855f7" if pct_uso < 70 else ("#f59e0b" if pct_uso < 90 else "#ff4b6e"),
                                       label=f"{pct_uso:.0f}%")
            
            st.markdown(f"""
            <div class="glass-card" style="border-left: 4px solid {color_from};">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;">
                    <div>
                        <div style="font-size:0.68rem;color:var(--text2);text-transform:uppercase;font-weight:600;">Fatura {mes_sel:02d}/{ano_sel}</div>
                        <div style="font-size:1.6rem;font-weight:900;color:{'var(--red)' if fatura_mensal > 0 else 'var(--green)'};">{fmt(fatura_mensal)}</div>
                        <div style="font-size:0.7rem;color:var(--text3);">Vence dia {c['dia_vencimento']} · Período: {data_ini} a {data_fim}</div>
                    </div>
                    <div style="text-align:center;">
                        {ring_html}
                        <div style="font-size:0.55rem;color:var(--text3);margin-top:0.2rem;">Limite<br>usado</div>
                    </div>
                </div>
                <div style="display:flex;justify-content:space-between;font-size:0.8rem;margin-bottom:0.4rem;color:var(--text2);">
                    <span>Disponível: <strong style="color:var(--green);">{fmt(limite_disp)}</strong></span>
                    <span>Usado: <strong>{fmt(fatura_total)}</strong> / {fmt(limite)}</span>
                </div>
                <div class="rule-bar-bg" style="height:6px;">
                    <div class="rule-bar-fill" style="width:{pct_uso}%;background:linear-gradient(90deg,{color_from},{color_to});"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        if fatura_mensal > 0:
            with st.expander(f"💳 Pagar Fatura de {mes_sel:02d}/{ano_sel} - {c['nome']}"):
                with st.form(f"pagar_fatura_{mes_sel}_{c['id']}"):
                    pf1, pf2 = st.columns(2)
                    with pf1:
                        val_pag = st.number_input(
                            "Valor do Pagamento (R$)",
                            min_value=0.01, value=float(fatura_mensal), step=10.0, format="%.2f",
                        )
                    with pf2:
                        outras_contas = conn.execute(
                            "SELECT id, nome FROM contas WHERE tipo NOT IN ('Cartão de Crédito', 'Reserva de Emergência')"
                        ).fetchall()
                        if outras_contas:
                            conta_pag = st.selectbox("Pagar usando a conta", outras_contas, format_func=lambda x: x[1])
                        else:
                            st.warning("Nenhuma conta corrente disponível.")
                            conta_pag = None

                    if st.form_submit_button("Confirmar Pagamento"):
                        if conta_pag:
                            data_hoje = date.today().strftime("%Y-%m-%d")
                            conn.execute(
                                "INSERT INTO transacoes (tipo, descricao, valor, data, conta_id) VALUES ('despesa', ?, ?, ?, ?)",
                                (f"Pagamento Fatura {mes_sel:02d}/{ano_sel} - {c['nome']}", val_pag, data_hoje, conta_pag[0]),
                            )
                            conn.execute(
                                "INSERT INTO transacoes (tipo, descricao, valor, data, conta_id) VALUES ('receita', ?, ?, ?, ?)",
                                (f"Pagamento Recebido - Fatura {mes_sel:02d}/{ano_sel}", val_pag, data_hoje, c["id"]),
                            )
                            conn.commit()
                            st.success("Fatura paga com sucesso!")
                            st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
