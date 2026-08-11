"""
tabs/cartoes.py — Aba de Cartões de Crédito.
"""
import streamlit as st
import pandas as pd
from datetime import date

from core.utils import fmt
from core.database import saldo_conta, read_sql
from components.cards import sec


def render(ctx):
    """Renderiza a aba Cartões de Crédito."""
    conn = ctx["conn"]

    sec("💳", "Seus Cartões de Crédito")
    cartoes = read_sql("SELECT * FROM contas WHERE tipo = 'Cartão de Crédito'", conn)

    if cartoes.empty:
        st.info("Você ainda não tem nenhum cartão de crédito cadastrado. Vá até a aba 'Contas' para adicionar um.")
        return

    for _, c in cartoes.iterrows():
        saldo = saldo_conta(conn, c["id"])
        fatura_atual = -saldo if saldo < 0 else 0
        limite = c["limite_cartao"] or 0
        limite_disp = limite - fatura_atual

        cor_fat = "var(--red)" if fatura_atual > 0 else "var(--green)"
        pct_uso = min(100, (fatura_atual / limite) * 100 if limite > 0 else 0)

        st.markdown(f'''
        <div class="glass-card" style="margin-bottom: 0.5rem; border-left: 4px solid var(--purple);">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div style="display:flex; align-items:center; gap: 1rem;">
                    <div class="acc-icon-wrap" style="background: rgba(168,85,247,0.15); font-size:1.5rem; width:48px; height:48px; display:flex; align-items:center; justify-content:center; border-radius:12px;">{c["icone"]}</div>
                    <div>
                        <div style="font-size: 1.1rem; font-weight: 700;">{c["nome"]}</div>
                        <div style="font-size: 0.8rem; color: var(--text2);">Vence dia {c["dia_vencimento"]} (Fecha dia {c["dia_fechamento"]})</div>
                    </div>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 0.75rem; color: var(--text2); text-transform: uppercase; font-weight: 600;">Fatura Atual</div>
                    <div style="font-size: 1.6rem; font-weight: 800; color: {cor_fat};">{fmt(fatura_atual)}</div>
                </div>
            </div>
            <div style="margin-top: 1.2rem;">
                <div style="display:flex; justify-content:space-between; font-size: 0.8rem; margin-bottom: 0.4rem; color: var(--text2);">
                    <span>Limite Disponível: <strong style="color:var(--green);">{fmt(limite_disp)}</strong></span>
                    <span>Limite Total: <strong>{fmt(limite)}</strong></span>
                </div>
                <div class="rule-bar-bg" style="height: 6px;">
                    <div class="rule-bar-fill" style="width: {pct_uso}%; background: var(--purple);"></div>
                </div>
            </div>
        </div>
        ''', unsafe_allow_html=True)

        if fatura_atual > 0:
            with st.expander(f"💳 Pagar Fatura - {c['nome']}"):
                with st.form(f"pagar_fatura_{c['id']}"):
                    pf1, pf2 = st.columns(2)
                    with pf1:
                        val_pag = st.number_input(
                            "Valor do Pagamento (R$)",
                            min_value=0.01, value=float(fatura_atual), step=10.0, format="%.2f",
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
                                (f"Pagamento Fatura {c['nome']}", val_pag, data_hoje, conta_pag[0]),
                            )
                            conn.execute(
                                "INSERT INTO transacoes (tipo, descricao, valor, data, conta_id) VALUES ('receita', ?, ?, ?, ?)",
                                ("Pagamento Recebido", val_pag, data_hoje, c["id"]),
                            )
                            conn.commit()
                            st.success("Fatura paga com sucesso!")
                            st.rerun()
