"""
components/cards.py — Componentes HTML reutilizáveis para o dashboard.
"""
import streamlit as st


def metric_card(icon_emoji, icon_class, label, value, value_class, badge="", badge_class=""):
    """Gera HTML de um card de métrica premium."""
    badge_html = f'<span class="metric-badge {badge_class}">{badge}</span>' if badge else ""
    return (
        f'<div class="metric-card">'
        f'<div class="metric-icon {icon_class}">{icon_emoji}</div>'
        f'<div class="metric-label">{label}</div>'
        f'<p class="metric-value {value_class}">{value}</p>'
        f'{badge_html}'
        f'</div>'
    )


def sec(icon, title):
    """Renderiza header de seção com linha decorativa."""
    st.markdown(
        f'<div class="sec-header"><h3>{icon} {title}</h3>'
        f'<div class="sec-line"></div></div>',
        unsafe_allow_html=True,
    )
