"""
components/cards.py — Componentes HTML reutilizáveis premium para o dashboard.
Versão 2.0: sparklines, ring progress, hero cards, tooltips, empty states, badges.
"""
import streamlit as st
import html as html_module


def metric_card(icon_emoji, icon_class, label, value, value_class, badge="", badge_class="", trend=None, trend_dir="neutral"):
    """Gera HTML de um card de métrica premium com glow e trend indicator."""
    badge_html = f'<span class="metric-badge {badge_class}">{badge}</span>' if badge else ""
    
    trend_html = ""
    if trend is not None:
        t_cls = "up" if trend_dir == "up" else ("down" if trend_dir == "down" else "neutral")
        arrow = "↑" if trend_dir == "up" else ("↓" if trend_dir == "down" else "→")
        trend_html = f'<span class="metric-trend {t_cls}">{arrow} {trend}</span>'
    
    return (
        f'<div class="metric-card">'
        f'<div class="metric-glow {icon_class}"></div>'
        f'<div class="metric-icon {icon_class}">{icon_emoji}</div>'
        f'<div class="metric-label">{label}</div>'
        f'<p class="metric-value {value_class}">{value}</p>'
        f'{trend_html}'
        f'{badge_html}'
        f'</div>'
    )


def sec(icon, title, tooltip=None):
    """Renderiza header de seção com linha decorativa e tooltip opcional."""
    tooltip_html = ""
    if tooltip:
        tooltip_html = (
            f'<span class="tooltip-help">?'
            f'<span class="tooltip-content">{html_module.escape(tooltip)}</span>'
            f'</span>'
        )
    st.markdown(
        f'<div class="sec-header"><h3>{icon} {title}{tooltip_html}</h3>'
        f'<div class="sec-line"></div></div>',
        unsafe_allow_html=True,
    )


def hero_card(label, value, change_pct=None, change_label="vs mês anterior", sub_text="", live=True):
    """Renderiza hero card de destaque (patrimônio líquido, etc)."""
    live_html = '<span class="live-dot"></span> Atualizado' if live else ""
    
    change_html = ""
    if change_pct is not None:
        cls = "positive" if change_pct >= 0 else "negative"
        arrow = "↑" if change_pct >= 0 else "↓"
        change_html = f'<div class="hero-change {cls}">{arrow} {abs(change_pct):.1f}% {change_label}</div>'
    
    return f"""
    <div class="hero-card">
        <div class="hero-label">{label} <span style="margin-left:auto;font-size:0.6rem;color:var(--text3);">{live_html}</span></div>
        <div class="hero-value">{value}</div>
        {change_html}
        <div class="hero-sub">{sub_text}</div>
    </div>
    """


def alert_card(icon, message, level="info"):
    """Renderiza card de alerta inteligente (critical, warning, positive, info)."""
    return f"""
    <div class="alert-card {level}">
        <span class="alert-icon">{icon}</span>
        <span class="alert-text">{message}</span>
    </div>
    """


def activity_item(icon, desc, meta, value, is_income=False):
    """Renderiza item do feed de atividade recente."""
    cls = "inc" if is_income else "exp"
    sinal = "+" if is_income else "-"
    return f"""
    <div class="activity-item {cls}">
        <div>
            <div class="activity-desc">{icon} {html_module.escape(desc)}</div>
            <div class="activity-meta">{html_module.escape(meta)}</div>
        </div>
        <div class="activity-val {cls}">{sinal} {value}</div>
    </div>
    """


def ring_progress(percentage, size=70, stroke=6, color="var(--green)", label=""):
    """Gera SVG de progresso circular (ring) como img base64."""
    import base64
    radius = (size - stroke) / 2
    circumference = 2 * 3.14159 * radius
    offset = circumference - (percentage / 100) * circumference
    
    # Resolver var(--green) para cor hex, pois SVG base64 não tem acesso ao CSS
    color_map = {
        "var(--green)": "#00d4aa",
        "var(--red)": "#ff4b6e",
        "var(--blue)": "#4e8cff",
        "var(--amber)": "#f59e0b",
        "var(--purple)": "#a855f7",
        "var(--cyan)": "#06b6d4",
    }
    svg_color = color_map.get(color, color)
    
    svg_raw = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}">'
        f'<circle cx="{size/2}" cy="{size/2}" r="{radius}" '
        f'fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="{stroke}"/>'
        f'<circle cx="{size/2}" cy="{size/2}" r="{radius}" '
        f'fill="none" stroke="{svg_color}" stroke-width="{stroke}" '
        f'stroke-linecap="round" '
        f'stroke-dasharray="{circumference}" '
        f'stroke-dashoffset="{offset}" '
        f'transform="rotate(-90 {size/2} {size/2})"/>'
        f'</svg>'
    )
    b64 = base64.b64encode(svg_raw.encode()).decode()
    
    display_label = label if label else f'{percentage:.0f}%'
    
    return f"""
    <div class="ring-progress" style="width:{size}px;height:{size}px;position:relative;">
        <img src="data:image/svg+xml;base64,{b64}" width="{size}" height="{size}" style="display:block;">
        <span class="ring-value" style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);font-size:0.7rem;font-weight:700;color:#f0f2f5;">{display_label}</span>
    </div>
    """


def empty_state(icon, title, description, cta_text="", cta_action=""):
    """Renderiza estado vazio estilizado com animação."""
    cta_html = ""
    if cta_text:
        cta_html = f'<div style="margin-top:0.5rem"><span class="empty-cta">{cta_text}</span></div>'
    
    return f"""
    <div class="empty-state">
        <div class="empty-icon">{icon}</div>
        <div class="empty-title">{title}</div>
        <div class="empty-desc">{description}</div>
        {cta_html}
    </div>
    """


def badge_card(emoji, title, desc, color):
    """Renderiza card de conquista/badge com glow."""
    return f"""
    <div class="badge-card">
        <div class="badge-glow" style="background:{color};"></div>
        <div class="badge-emoji">{emoji}</div>
        <div class="badge-title" style="color:{color};">{title}</div>
        <div class="badge-desc">{desc}</div>
    </div>
    """


def streak_bar(count, label="dias seguidos registrando"):
    """Renderiza barra de streak (gamificação)."""
    return f"""
    <div class="streak-bar">
        <span class="streak-fire">🔥</span>
        <span class="streak-count">{count}</span>
        <span class="streak-label">{label}</span>
    </div>
    """


def tooltip(text, explanation):
    """Gera span com tooltip explicativo inline."""
    return f'{text}<span class="tooltip-help">?<span class="tooltip-content">{html_module.escape(explanation)}</span></span>'


def calendar_day_cell(day, amount=0, max_amount=1, is_today=False, has_bill=False, is_empty=False):
    """Gera célula do calendário heatmap."""
    if is_empty:
        return '<div class="cal-day empty"></div>'
    
    intensity = min(amount / max_amount, 1.0) if max_amount > 0 else 0
    r = int(11 + intensity * (255 - 11))
    g = int(14 + intensity * (75 - 14))
    b = int(20 + intensity * (110 - 20))
    bg = f"rgba({r},{g},{b},{0.15 + intensity * 0.4})"
    
    today_cls = "today" if is_today else ""
    bill_html = '<div class="cal-bill-dot"></div>' if has_bill else ""
    
    from core.utils import fmt
    amount_html = f'<div class="cal-amount">{fmt(amount)}</div>' if amount > 0 else ""
    
    return f"""
    <div class="cal-day {today_cls}" style="background:{bg};" title="Dia {day}: {fmt(amount) if amount > 0 else 'R$ 0,00'}">
        {bill_html}
        <span>{day}</span>
        {amount_html}
    </div>
    """


def credit_card_visual(bank_name, icon, bill_value, due_day, color_from="#a855f7", color_to="#6d28d9"):
    """Renderiza visual de cartão de crédito 3D."""
    return f"""
    <div class="credit-card-visual" style="background: linear-gradient(135deg, {color_from}, {color_to});">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;">
            <div>
                <div class="cc-bank">{icon} {bank_name}</div>
            </div>
            <div class="cc-chip"></div>
        </div>
        <div>
            <div class="cc-number">•••• •••• •••• ••••</div>
        </div>
        <div style="display:flex;justify-content:space-between;align-items:flex-end;">
            <div>
                <div class="cc-label">Fatura Atual</div>
                <div class="cc-value" style="font-size:1.2rem;font-weight:900;">{bill_value}</div>
            </div>
            <div style="text-align:right;">
                <div class="cc-label">Vencimento</div>
                <div class="cc-value">Dia {due_day}</div>
            </div>
        </div>
    </div>
    """
