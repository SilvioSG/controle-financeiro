"""
components/glossario.py — Glossário financeiro integrado para a sidebar.
"""
import streamlit as st
from components.tooltip_helper import EXPLICACOES


# Organização por categoria para melhor navegação
GLOSSARIO_CATEGORIAS = {
    "💰 Seu Dinheiro": [
        ("Receita", "receita"),
        ("Despesa", "despesa"),
        ("Saldo", "saldo"),
        ("Balanço Líquido", "balanco"),
        ("Patrimônio Líquido", "patrimonio"),
    ],
    "📊 Planejamento": [
        ("Regra 50-30-20", "regra503020"),
        ("Orçamento Base Zero", "base_zero"),
        ("Reserva de Emergência", "reserva"),
        ("Score de Saúde", "score"),
        ("Transação Recorrente", "recorrente"),
    ],
    "📈 Investimentos": [
        ("CDI", "cdi"),
        ("Taxa Selic", "selic"),
        ("IPCA", "ipca"),
        ("FGC", "fgc"),
        ("Tesouro Selic", "tesouro_selic"),
        ("CDB", "cdb"),
        ("LCI / LCA", "lci_lca"),
        ("IR Regressivo", "ir_regressivo"),
    ],
    "🏢 Impostos": [
        ("Simples Nacional", "simples"),
    ],
}


def render_glossario():
    """Renderiza o glossário financeiro na sidebar ou em expander."""
    st.markdown("""
        <div style="margin-bottom: 0.5rem;">
            <span style="font-size: 0.72rem; color: var(--text2); text-transform: uppercase; letter-spacing: 0.8px; font-weight: 600;">
                📖 Glossário Financeiro
            </span>
            <div style="font-size: 0.68rem; color: var(--text3); margin-top: 0.2rem;">
                Entenda os termos usados no app
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    busca = st.text_input("🔍 Buscar termo...", key="busca_glossario", label_visibility="collapsed", placeholder="Buscar termo...")
    
    for categoria, termos in GLOSSARIO_CATEGORIAS.items():
        termos_filtrados = termos
        if busca.strip():
            busca_lower = busca.strip().lower()
            termos_filtrados = [
                (nome, chave) for nome, chave in termos
                if busca_lower in nome.lower() or busca_lower in EXPLICACOES.get(chave, "").lower()
            ]
        
        if not termos_filtrados:
            continue
            
        st.markdown(f"**{categoria}**")
        for nome, chave in termos_filtrados:
            explicacao = EXPLICACOES.get(chave, "")
            if explicacao:
                st.markdown(f"""
                    <div class="glossary-term">
                        <div class="glossary-word">{nome}</div>
                        <div class="glossary-def">{explicacao}</div>
                    </div>
                """, unsafe_allow_html=True)
