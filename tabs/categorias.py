"""
tabs/categorias.py — Aba de Categorias (listar, criar, editar, excluir).
"""
import streamlit as st
import pandas as pd

from components.cards import sec
from core.database import read_sql


def render(ctx):
    """Renderiza a aba Categorias."""
    conn = ctx["conn"]

    ca_all = read_sql("SELECT * FROM categorias ORDER BY tipo, nome", conn)

    if not ca_all.empty:
        sec("🔴", "Despesa")
        cd2 = ca_all[ca_all["tipo"].isin(["despesa", "ambos"])]
        cols = st.columns(4)
        for i, (_, c) in enumerate(cd2.iterrows()):
            with cols[i % 4]:
                cc, cx = st.columns([5, 1])
                with cc:
                    st.markdown(
                        f'<div class="cat-chip">{c["icone"]} {c["nome"]}</div>',
                        unsafe_allow_html=True,
                    )
                with cx:
                    if st.button("✕", key=f"dc_{c['id']}"):
                        conn.execute("DELETE FROM categorias WHERE id=?", (c["id"],))
                        conn.commit()
                        st.rerun()
                with st.expander("✏️", expanded=False):
                    en_cat = st.text_input("Novo nome", value=c["nome"], key=f"en_cat_{c['id']}")
                    if st.button("Salvar", key=f"es_cat_{c['id']}", type="primary"):
                        if en_cat.strip():
                            conn.execute("UPDATE categorias SET nome=? WHERE id=?", (en_cat.strip(), c["id"]))
                            conn.commit()
                            st.rerun()

        sec("🟢", "Receita")
        cr = ca_all[ca_all["tipo"].isin(["receita", "ambos"])]
        cols2 = st.columns(4)
        for i, (_, c) in enumerate(cr.iterrows()):
            with cols2[i % 4]:
                cc2, cx2 = st.columns([5, 1])
                with cc2:
                    st.markdown(
                        f'<div class="cat-chip">{c["icone"]} {c["nome"]}</div>',
                        unsafe_allow_html=True,
                    )
                with cx2:
                    if st.button("✕", key=f"dc2_{c['id']}"):
                        conn.execute("DELETE FROM categorias WHERE id=?", (c["id"],))
                        conn.commit()
                        st.rerun()
                with st.expander("✏️", expanded=False):
                    en_cat = st.text_input("Novo nome", value=c["nome"], key=f"en_cat_{c['id']}_r")
                    if st.button("Salvar", key=f"es_cat_{c['id']}_r", type="primary"):
                        if en_cat.strip():
                            conn.execute("UPDATE categorias SET nome=? WHERE id=?", (en_cat.strip(), c["id"]))
                            conn.commit()
                            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Nova Categoria ────────────────────────────────────────────────
    sec("➕", "Nova Categoria")
    with st.form("form_cat", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            nm = st.text_input("Nome", placeholder="Ex: Pets...")
        with c2:
            ic2 = st.selectbox("Ícone", [
                "🍔", "🚗", "🏠", "💊", "📚", "🎮", "👕", "📺", "🛒", "💳",
                "🐾", "✈️", "🎵", "🏋️", "💇", "📱", "💰", "💻", "📈", "🎁", "💵", "📦",
            ])
        with c3:
            tp = st.selectbox(
                "Tipo", ["despesa", "receita", "ambos"],
                format_func=lambda x: {"despesa": "🔴 Despesa", "receita": "🟢 Receita", "ambos": "🔄 Ambos"}[x],
            )
        if st.form_submit_button("💾 Criar", width='stretch'):
            if nm.strip():
                conn.execute("INSERT INTO categorias (nome,icone,tipo) VALUES (?,?,?)", (nm.strip(), ic2, tp))
                conn.commit()
                st.success("✅ Criada!")
                st.rerun()
