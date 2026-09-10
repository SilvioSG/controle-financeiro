"""
components/styles.py — CSS premium do dashboard financeiro.
Versão 2.0: Glassmorphism avançado, micro-animações, skeleton loading, tipografia refinada.
"""
import streamlit as st


def inject_css():
    """Injeta o CSS completo do tema premium dark v2."""
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* ═══════════════════════════════════════════════════════════════════
   DESIGN TOKENS
   ═══════════════════════════════════════════════════════════════════ */
:root {
    /* Backgrounds */
    --bg: #0b0e14;
    --bg-elevated: #101520;
    --card: rgba(18,22,32,0.75);
    --card-solid: #121620;
    --card-hover: rgba(26,32,48,0.92);
    --glass: rgba(255,255,255,0.025);
    --glass-strong: rgba(255,255,255,0.05);

    /* Borders */
    --border: rgba(255,255,255,0.06);
    --border-light: rgba(255,255,255,0.12);
    --border-focus: rgba(0,212,170,0.4);

    /* Accent colors */
    --green: #00d4aa;
    --green-dim: #00a888;
    --green-glow: rgba(0,212,170,0.15);
    --green-glow-strong: rgba(0,212,170,0.25);

    --red: #ff4b6e;
    --red-dim: #cc3d58;
    --red-glow: rgba(255,75,110,0.15);

    --blue: #4e8cff;
    --blue-dim: #3a6fd4;
    --blue-glow: rgba(78,140,255,0.15);

    --purple: #a855f7;
    --purple-dim: #8b3fd4;
    --purple-glow: rgba(168,85,247,0.15);

    --amber: #f59e0b;
    --amber-dim: #d97706;
    --amber-glow: rgba(245,158,11,0.15);

    --cyan: #06b6d4;
    --cyan-glow: rgba(6,182,212,0.15);

    /* Typography */
    --text: #f0f2f5;
    --text2: #8b95a5;
    --text3: #5a6478;
    --text4: #3d4555;

    /* Spacing */
    --sp-xs: 0.25rem;
    --sp-sm: 0.5rem;
    --sp-md: 1rem;
    --sp-lg: 1.5rem;
    --sp-xl: 2rem;

    /* Shadows */
    --shadow-sm: 0 2px 8px rgba(0,0,0,0.2);
    --shadow-md: 0 8px 24px rgba(0,0,0,0.3);
    --shadow-lg: 0 16px 48px rgba(0,0,0,0.4);
    --shadow-glow-green: 0 0 20px rgba(0,212,170,0.15);
    --shadow-glow-blue: 0 0 20px rgba(78,140,255,0.15);
    --shadow-glow-red: 0 0 20px rgba(255,75,110,0.15);

    /* Transitions */
    --ease-smooth: cubic-bezier(0.4,0,0.2,1);
    --ease-bounce: cubic-bezier(0.34,1.56,0.64,1);

    /* Radius */
    --radius-sm: 8px;
    --radius-md: 12px;
    --radius-lg: 16px;
    --radius-xl: 20px;
    --radius-full: 50%;
}

/* ═══════════════════════════════════════════════════════════════════
   GLOBAL RESET & TYPOGRAPHY
   ═══════════════════════════════════════════════════════════════════ */
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    text-rendering: optimizeLegibility;
}

/* Scrollbar Premium */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.08); border-radius: 10px; transition: background 0.3s; }
::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.18); }

/* Seleção de texto */
::selection { background: rgba(0,212,170,0.3); color: #fff; }

/* ═══════════════════════════════════════════════════════════════════
   ANIMATIONS
   ═══════════════════════════════════════════════════════════════════ */
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}
@keyframes fadeInLeft {
    from { opacity: 0; transform: translateX(-15px); }
    to { opacity: 1; transform: translateX(0); }
}
@keyframes slideUp {
    from { opacity: 0; transform: translateY(15px); }
    to { opacity: 1; transform: translateY(0); }
}
@keyframes pulseGlow {
    0%, 100% { box-shadow: 0 0 5px rgba(0,212,170,0.2); }
    50% { box-shadow: 0 0 20px rgba(0,212,170,0.4); }
}
@keyframes shimmer {
    0%, 100% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
}
@keyframes shimmerLoad {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
}
@keyframes pulseDot {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.5; transform: scale(0.8); }
}
@keyframes borderGlow {
    0%, 100% { border-color: rgba(0,212,170,0.2); }
    50% { border-color: rgba(0,212,170,0.5); }
}
@keyframes float {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-5px); }
}
@keyframes progressFill {
    from { width: 0%; }
}
@keyframes scaleIn {
    from { opacity: 0; transform: scale(0.9); }
    to { opacity: 1; transform: scale(1); }
}
@keyframes rotateGlow {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* Stagger animation helper classes */
.stagger-1 { animation-delay: 0.05s; }
.stagger-2 { animation-delay: 0.1s; }
.stagger-3 { animation-delay: 0.15s; }
.stagger-4 { animation-delay: 0.2s; }
.stagger-5 { animation-delay: 0.25s; }

/* ═══════════════════════════════════════════════════════════════════
   GLASS CARD (Base Component)
   ═══════════════════════════════════════════════════════════════════ */
.glass-card {
    background: var(--card);
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 1.4rem 1.5rem;
    transition: all 0.4s var(--ease-smooth);
    position: relative;
    overflow: hidden;
}
.glass-card::before {
    content:'';
    position: absolute;
    top:0; left:0; right:0;
    height:1px;
    background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.08) 50%, transparent 100%);
}
.glass-card:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-lg);
    border-color: var(--border-light);
    background: var(--card-hover);
}

/* ═══════════════════════════════════════════════════════════════════
   HERO CARD (Patrimônio / destaque principal)
   ═══════════════════════════════════════════════════════════════════ */
.hero-card {
    background: linear-gradient(135deg, rgba(18,22,32,0.9) 0%, rgba(14,18,28,0.8) 50%, rgba(18,22,32,0.9) 100%);
    backdrop-filter: blur(30px);
    border: 1px solid var(--border);
    border-radius: var(--radius-xl);
    padding: 1.8rem 2rem;
    position: relative;
    overflow: hidden;
    animation: fadeInUp 0.6s var(--ease-smooth) forwards;
}
.hero-card::before {
    content:'';
    position: absolute;
    top:0; left:0; right:0;
    height:3px;
    background: linear-gradient(90deg, var(--green), var(--blue), var(--purple));
    background-size: 200% 100%;
    animation: shimmer 3s ease-in-out infinite;
}
.hero-card::after {
    content:'';
    position: absolute;
    top: -50%; right: -20%;
    width: 300px; height: 300px;
    background: radial-gradient(circle, rgba(0,212,170,0.06) 0%, transparent 70%);
    border-radius: 50%;
    pointer-events: none;
}
.hero-label { font-size: 0.7rem; font-weight: 600; color: var(--text2); text-transform: uppercase; letter-spacing: 1.2px; margin-bottom: 0.3rem; display: flex; align-items: center; gap: 0.4rem; }
.hero-value { font-size: 2.4rem; font-weight: 900; color: var(--text); line-height: 1.15; letter-spacing: -0.02em; }
.hero-change { display: inline-flex; align-items: center; gap: 0.3rem; font-size: 0.78rem; font-weight: 700; padding: 0.2rem 0.6rem; border-radius: 20px; margin-top: 0.4rem; }
.hero-change.positive { color: var(--green); background: var(--green-glow); }
.hero-change.negative { color: var(--red); background: var(--red-glow); }
.hero-sub { font-size: 0.72rem; color: var(--text3); margin-top: 0.5rem; }
.live-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--green); display: inline-block; animation: pulseDot 2s ease-in-out infinite; }

/* ═══════════════════════════════════════════════════════════════════
   METRIC CARD (KPIs)
   ═══════════════════════════════════════════════════════════════════ */
.metric-card {
    background: var(--card);
    backdrop-filter: blur(20px);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 1.2rem 1.3rem;
    transition: all 0.4s var(--ease-smooth);
    position: relative;
    overflow: hidden;
    animation: fadeInUp 0.5s var(--ease-smooth) forwards;
    opacity: 0;
}
.metric-card:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-lg);
    border-color: var(--border-light);
}
.metric-card .metric-glow {
    position: absolute;
    top: -20px; right: -20px;
    width: 80px; height: 80px;
    border-radius: 50%;
    filter: blur(30px);
    opacity: 0.15;
    pointer-events: none;
}
.metric-card .metric-glow.green { background: var(--green); }
.metric-card .metric-glow.red { background: var(--red); }
.metric-card .metric-glow.blue { background: var(--blue); }
.metric-card .metric-glow.amber { background: var(--amber); }
.metric-card .metric-glow.purple { background: var(--purple); }

.metric-icon {
    width: 40px; height: 40px;
    border-radius: var(--radius-md);
    display: flex; align-items: center; justify-content: center;
    font-size: 1.15rem;
    margin-bottom: 0.7rem;
    position: relative;
    z-index: 1;
}
.metric-icon.green { background: linear-gradient(135deg, #00d4aa, #00a888); box-shadow: 0 4px 12px rgba(0,212,170,0.25); }
.metric-icon.red { background: linear-gradient(135deg, #ff4b6e, #cc3d58); box-shadow: 0 4px 12px rgba(255,75,110,0.25); }
.metric-icon.blue { background: linear-gradient(135deg, #4e8cff, #3a6fd4); box-shadow: 0 4px 12px rgba(78,140,255,0.25); }
.metric-icon.amber { background: linear-gradient(135deg, #f59e0b, #d97706); box-shadow: 0 4px 12px rgba(245,158,11,0.25); }
.metric-icon.purple { background: linear-gradient(135deg, #a855f7, #8b3fd4); box-shadow: 0 4px 12px rgba(168,85,247,0.25); }

.metric-label {
    font-size: 0.65rem; font-weight: 600; color: var(--text2);
    text-transform: uppercase; letter-spacing: 0.9px;
    margin-bottom: 0.3rem;
}
.metric-value {
    font-size: 1.4rem; font-weight: 800;
    margin: 0; line-height: 1.2;
    white-space: nowrap; letter-spacing: -0.01em;
}
.metric-trend {
    display: inline-flex; align-items: center; gap: 0.2rem;
    font-size: 0.62rem; font-weight: 700;
    margin-top: 0.3rem; padding: 0.1rem 0.45rem;
    border-radius: 12px;
}
.metric-trend.up { color: var(--green); background: var(--green-glow); }
.metric-trend.down { color: var(--red); background: var(--red-glow); }
.metric-trend.neutral { color: var(--text3); background: rgba(255,255,255,0.04); }

.metric-badge {
    display: inline-block; padding: 0.15rem 0.55rem;
    border-radius: 20px; font-size: 0.62rem;
    font-weight: 600; margin-top: 0.35rem; letter-spacing: 0.3px;
}
.mv-green { color: var(--green); } .mb-green { background: var(--green-glow); color: var(--green); }
.mv-red { color: var(--red); } .mb-red { background: var(--red-glow); color: var(--red); }
.mv-blue { color: var(--blue); } .mb-blue { background: var(--blue-glow); color: var(--blue); }
.mv-amber { color: var(--amber); } .mb-amber { background: var(--amber-glow); color: var(--amber); }
.mv-purple { color: var(--purple); } .mb-purple { background: var(--purple-glow); color: var(--purple); }

/* Sparkline container inside metric card */
.metric-sparkline {
    margin-top: 0.6rem;
    height: 30px;
    position: relative;
    overflow: hidden;
    border-radius: 4px;
}
.metric-sparkline svg { width: 100%; height: 100%; }

/* ═══════════════════════════════════════════════════════════════════
   APP HEADER
   ═══════════════════════════════════════════════════════════════════ */
.app-header {
    background: linear-gradient(135deg, var(--card-solid) 0%, rgba(18,22,32,0.6) 100%);
    backdrop-filter: blur(24px);
    border: 1px solid var(--border);
    border-radius: var(--radius-xl);
    padding: 1.6rem 2rem;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
    animation: fadeInUp 0.5s var(--ease-smooth) forwards;
}
.app-header::before {
    content:'';
    position: absolute;
    top:0; left:0; right:0;
    height:3px;
    background: linear-gradient(90deg, var(--green), var(--blue), var(--purple), var(--amber));
    background-size: 300% 100%;
    animation: shimmer 4s ease-in-out infinite;
}
.app-header::after {
    content:'';
    position: absolute;
    bottom: -30%; right: -10%;
    width: 250px; height: 250px;
    background: radial-gradient(circle, rgba(78,140,255,0.04) 0%, transparent 70%);
    border-radius: 50%;
    pointer-events: none;
}
.app-header h1 {
    font-size: 1.6rem; font-weight: 800;
    margin: 0 0 0.15rem 0;
    color: #ffffff !important;
    letter-spacing: -0.02em;
}
.app-header h1 span {
    background: linear-gradient(135deg, #fff 0%, rgba(240,242,245,0.8) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.app-header p { color: var(--text2); font-size: 0.82rem; margin: 0; font-weight: 400; }

/* ═══════════════════════════════════════════════════════════════════
   SECTION HEADERS
   ═══════════════════════════════════════════════════════════════════ */
.sec-header {
    display: flex; align-items: center; gap: 0.6rem;
    margin: 1.8rem 0 1rem 0;
    animation: fadeInLeft 0.4s var(--ease-smooth) forwards;
}
.sec-header h3 {
    font-size: 0.95rem; font-weight: 700;
    color: var(--text); margin: 0;
    letter-spacing: -0.01em;
    white-space: nowrap;
}
.sec-header .sec-line {
    flex: 1; height: 1px;
    background: linear-gradient(90deg, var(--border-light), transparent);
}

/* ═══════════════════════════════════════════════════════════════════
   ALERT CARDS (Smart Alerts)
   ═══════════════════════════════════════════════════════════════════ */
.alert-card {
    background: var(--card);
    border-left: 3px solid;
    padding: 0.7rem 1.1rem;
    border-radius: var(--radius-sm);
    margin-bottom: 0.5rem;
    display: flex; align-items: center; gap: 0.7rem;
    animation: fadeInLeft 0.4s var(--ease-smooth) forwards;
    opacity: 0;
    transition: all 0.3s var(--ease-smooth);
}
.alert-card:hover { background: var(--card-hover); transform: translateX(3px); }
.alert-card.critical { border-color: var(--red); }
.alert-card.warning { border-color: var(--amber); }
.alert-card.positive { border-color: var(--green); }
.alert-card.info { border-color: var(--blue); }
.alert-icon { font-size: 1.15rem; flex-shrink: 0; }
.alert-text { font-size: 0.8rem; color: var(--text); line-height: 1.4; }

/* ═══════════════════════════════════════════════════════════════════
   TRANSACTION ITEMS (Feed)
   ═══════════════════════════════════════════════════════════════════ */
.tx-item {
    display: flex; align-items: center; justify-content: space-between;
    padding: 0.75rem 1.1rem;
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    margin-bottom: 0.35rem;
    transition: all 0.3s var(--ease-smooth);
    animation: slideUp 0.4s var(--ease-smooth) forwards;
}
.tx-item:hover {
    background: var(--card-hover);
    border-color: var(--border-light);
    transform: translateX(4px);
}
.tx-left { display: flex; align-items: center; gap: 0.75rem; }
.tx-cat-icon {
    width: 38px; height: 38px;
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.1rem;
    flex-shrink: 0;
}
.tx-cat-icon.inc-bg { background: var(--green-glow); }
.tx-cat-icon.exp-bg { background: var(--red-glow); }
.tx-desc { font-size: 0.85rem; font-weight: 500; color: var(--text); }
.tx-meta { font-size: 0.7rem; color: var(--text2); margin-top: 1px; display: flex; align-items: center; gap: 0.4rem; }
.tx-tag { display: inline-block; padding: 0.05rem 0.35rem; background: rgba(78,140,255,0.12); color: var(--blue); border-radius: 4px; font-size: 0.58rem; font-weight: 600; }
.tx-badge-recur { display: inline-block; padding: 0.05rem 0.35rem; background: rgba(168,85,247,0.12); color: var(--purple); border-radius: 4px; font-size: 0.58rem; font-weight: 600; }
.tx-badge-parcel { display: inline-block; padding: 0.05rem 0.35rem; background: rgba(245,158,11,0.12); color: var(--amber); border-radius: 4px; font-size: 0.58rem; font-weight: 600; }
.tx-amount { font-size: 0.92rem; font-weight: 700; text-align: right; white-space: nowrap; }
.tx-amount.inc { color: var(--green); }
.tx-amount.exp { color: var(--red); }
.day-header {
    font-size: 0.72rem; font-weight: 600; color: var(--text3);
    text-transform: uppercase; letter-spacing: 0.8px;
    padding: 0.5rem 0.2rem 0.3rem;
    border-bottom: 1px solid var(--border);
    margin-top: 0.8rem; margin-bottom: 0.4rem;
}

/* ═══════════════════════════════════════════════════════════════════
   ACTIVITY FEED (Dashboard mini-feed)
   ═══════════════════════════════════════════════════════════════════ */
.activity-feed {
    position: relative;
    padding-left: 1.2rem;
}
.activity-feed::before {
    content: '';
    position: absolute;
    left: 8px; top: 0; bottom: 0;
    width: 2px;
    background: linear-gradient(180deg, var(--border-light), transparent);
}
.activity-item {
    display: flex; align-items: center; justify-content: space-between;
    padding: 0.55rem 0.8rem;
    margin-bottom: 0.3rem;
    position: relative;
    border-radius: var(--radius-sm);
    transition: background 0.2s;
}
.activity-item:hover { background: rgba(255,255,255,0.02); }
.activity-item::before {
    content: '';
    position: absolute;
    left: -1.2rem;
    width: 8px; height: 8px;
    border-radius: 50%;
    border: 2px solid;
    background: var(--bg);
}
.activity-item.inc::before { border-color: var(--green); }
.activity-item.exp::before { border-color: var(--red); }
.activity-desc { font-size: 0.78rem; color: var(--text); font-weight: 500; }
.activity-meta { font-size: 0.65rem; color: var(--text3); }
.activity-val { font-size: 0.82rem; font-weight: 700; }
.activity-val.inc { color: var(--green); }
.activity-val.exp { color: var(--red); }

/* ═══════════════════════════════════════════════════════════════════
   ACCOUNT CARDS
   ═══════════════════════════════════════════════════════════════════ */
.account-card {
    background: var(--card);
    backdrop-filter: blur(20px);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 1.1rem 1.3rem;
    margin-bottom: 0.5rem;
    display: flex; align-items: center; justify-content: space-between;
    transition: all 0.3s var(--ease-smooth);
    animation: slideUp 0.4s var(--ease-smooth) forwards;
}
.account-card:hover { background: var(--card-hover); transform: translateX(4px); }
.acc-left { display: flex; align-items: center; gap: 0.8rem; }
.acc-icon-wrap {
    width: 44px; height: 44px;
    border-radius: var(--radius-md);
    display: flex; align-items: center; justify-content: center;
    font-size: 1.3rem;
    background: linear-gradient(135deg, rgba(78,140,255,0.15), rgba(78,140,255,0.05));
}
.acc-name { font-size: 0.9rem; font-weight: 600; color: var(--text); }
.acc-type { font-size: 0.7rem; color: var(--text2); }
.acc-balance { font-size: 1.05rem; font-weight: 700; }

/* ═══════════════════════════════════════════════════════════════════
   BUDGET ITEMS (Orçamento)
   ═══════════════════════════════════════════════════════════════════ */
.budget-item {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 1rem 1.3rem;
    margin-bottom: 0.5rem;
    animation: slideUp 0.4s var(--ease-smooth) forwards;
    transition: all 0.3s var(--ease-smooth);
}
.budget-item:hover { border-color: var(--border-light); }
.budget-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem; }
.budget-cat { font-size: 0.85rem; font-weight: 600; color: var(--text); }
.budget-vals { font-size: 0.75rem; color: var(--text2); }
.budget-bar-bg { width: 100%; height: 8px; border-radius: 8px; background: rgba(255,255,255,0.06); overflow: hidden; }
.budget-bar-fill { height: 100%; border-radius: 8px; transition: width 1.2s var(--ease-smooth); animation: progressFill 1.5s var(--ease-smooth); }
.budget-bar-fill.safe { background: linear-gradient(90deg, #00d4aa, #00b894); }
.budget-bar-fill.warn { background: linear-gradient(90deg, #f59e0b, #f97316); }
.budget-bar-fill.over { background: linear-gradient(90deg, #ff4b6e, #ef4444); }

/* ═══════════════════════════════════════════════════════════════════
   CATEGORY CHIPS
   ═══════════════════════════════════════════════════════════════════ */
.cat-chip {
    display: inline-flex; align-items: center; gap: 0.4rem;
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 0.55rem 1rem;
    margin: 0.2rem;
    font-size: 0.82rem;
    color: var(--text);
    transition: all 0.25s var(--ease-smooth);
}
.cat-chip:hover { background: var(--card-hover); border-color: var(--border-light); transform: translateY(-1px); }

/* ═══════════════════════════════════════════════════════════════════
   GOAL CARDS (Metas) — Ring Progress
   ═══════════════════════════════════════════════════════════════════ */
.goal-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 1.2rem 1.4rem;
    margin-bottom: 0.6rem;
    animation: fadeInUp 0.5s var(--ease-smooth) forwards;
    transition: all 0.3s var(--ease-smooth);
}
.goal-card:hover { border-color: var(--border-light); }
.goal-bar-bg {
    width: 100%; height: 10px;
    border-radius: 10px;
    background: rgba(255,255,255,0.06);
    overflow: hidden;
    margin: 0.5rem 0;
}
.goal-bar-fill {
    height: 100%; border-radius: 10px;
    transition: width 1.2s var(--ease-smooth);
    animation: progressFill 1.5s var(--ease-smooth);
}
.goal-bar-fill.g-green { background: linear-gradient(90deg, #00d4aa, #00b894); }
.goal-bar-fill.g-amber { background: linear-gradient(90deg, #f59e0b, #f97316); }
.goal-bar-fill.g-red { background: linear-gradient(90deg, #ff4b6e, #ef4444); }

/* Ring progress component */
.ring-progress {
    position: relative;
    display: inline-flex;
    align-items: center;
    justify-content: center;
}
.ring-progress svg { transform: rotate(-90deg); }
.ring-progress .ring-value {
    position: absolute;
    font-size: 0.85rem;
    font-weight: 800;
    color: var(--text);
}

/* ═══════════════════════════════════════════════════════════════════
   TOP EXPENSES
   ═══════════════════════════════════════════════════════════════════ */
.top-exp {
    display: flex; align-items: center; justify-content: space-between;
    padding: 0.55rem 0;
    border-bottom: 1px solid var(--border);
    transition: all 0.2s;
}
.top-exp:last-child { border-bottom: none; }
.top-exp:hover { padding-left: 0.3rem; }
.top-exp-left { display: flex; align-items: center; gap: 0.6rem; }
.top-exp-rank {
    width: 22px; height: 22px;
    border-radius: 6px;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.65rem; font-weight: 700;
    background: rgba(255,255,255,0.05);
    color: var(--text2);
}
.top-exp-name { font-size: 0.82rem; color: var(--text); font-weight: 500; }
.top-exp-val { font-size: 0.82rem; color: var(--red); font-weight: 700; }

/* ═══════════════════════════════════════════════════════════════════
   INSIGHT CARDS
   ═══════════════════════════════════════════════════════════════════ */
.insight-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.5rem;
    display: flex; align-items: flex-start; gap: 0.8rem;
    animation: fadeInUp 0.5s var(--ease-smooth) forwards;
    transition: all 0.3s var(--ease-smooth);
    opacity: 0;
}
.insight-card:nth-child(1) { animation-delay: 0s; }
.insight-card:nth-child(2) { animation-delay: 0.08s; }
.insight-card:nth-child(3) { animation-delay: 0.16s; }
.insight-card:nth-child(4) { animation-delay: 0.24s; }
.insight-card:hover { background: var(--card-hover); transform: translateX(4px); }
.insight-icon { font-size: 1.4rem; flex-shrink: 0; margin-top: 0.1rem; }
.insight-text { font-size: 0.82rem; color: var(--text); line-height: 1.5; }
.insight-text strong { color: var(--green); }
.insight-label { font-size: 0.65rem; color: var(--text3); text-transform: uppercase; letter-spacing: 0.5px; margin-top: 0.3rem; }

.insight-priority {
    display: inline-block;
    padding: 0.1rem 0.4rem;
    border-radius: 4px;
    font-size: 0.55rem;
    font-weight: 700;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    margin-bottom: 0.3rem;
}
.insight-priority.critical { background: var(--red-glow); color: var(--red); }
.insight-priority.warning { background: var(--amber-glow); color: var(--amber); }
.insight-priority.positive { background: var(--green-glow); color: var(--green); }

/* ═══════════════════════════════════════════════════════════════════
   RULE 50-30-20 BARS
   ═══════════════════════════════════════════════════════════════════ */
.rule-bar-wrap { margin-bottom: 0.8rem; }
.rule-bar-label { display: flex; justify-content: space-between; margin-bottom: 0.3rem; }
.rule-bar-name { font-size: 0.78rem; font-weight: 600; color: var(--text); }
.rule-bar-vals { font-size: 0.72rem; color: var(--text2); }
.rule-bar-bg {
    width: 100%; height: 10px;
    border-radius: 10px;
    background: rgba(255,255,255,0.06);
    overflow: hidden;
    position: relative;
}
.rule-bar-fill { height: 100%; border-radius: 10px; transition: width 1s ease; animation: progressFill 1.2s var(--ease-smooth); }
.rule-bar-ideal { position: absolute; top: 0; height: 100%; width: 2px; background: #fff; opacity: 0.5; }

/* ═══════════════════════════════════════════════════════════════════
   CALENDAR HEATMAP
   ═══════════════════════════════════════════════════════════════════ */
.cal-grid {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 3px;
}
.cal-header {
    text-align: center;
    font-size: 0.6rem;
    font-weight: 700;
    color: var(--text3);
    text-transform: uppercase;
    padding: 0.3rem 0;
}
.cal-day {
    aspect-ratio: 1;
    border-radius: 6px;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    font-size: 0.65rem;
    font-weight: 600;
    color: var(--text2);
    transition: all 0.2s;
    cursor: default;
    border: 1px solid transparent;
    position: relative;
}
.cal-day:hover { border-color: var(--border-light); transform: scale(1.1); z-index: 2; }
.cal-day.today { border-color: var(--green); color: var(--green); font-weight: 800; }
.cal-day.empty { opacity: 0; pointer-events: none; }
.cal-day .cal-amount { font-size: 0.5rem; margin-top: 1px; font-weight: 700; }
.cal-day .cal-bill-dot {
    position: absolute; top: 2px; right: 2px;
    width: 5px; height: 5px;
    border-radius: 50%;
    background: var(--red);
}

/* ═══════════════════════════════════════════════════════════════════
   CREDIT CARD VISUAL
   ═══════════════════════════════════════════════════════════════════ */
.credit-card-visual {
    width: 100%;
    max-width: 360px;
    aspect-ratio: 1.586;
    border-radius: 16px;
    padding: 1.5rem;
    position: relative;
    overflow: hidden;
    color: #fff;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    transition: transform 0.5s var(--ease-smooth);
    box-shadow: 0 20px 60px rgba(0,0,0,0.4);
}
.credit-card-visual:hover { transform: perspective(800px) rotateY(-5deg) rotateX(3deg); }
.credit-card-visual::before {
    content: '';
    position: absolute; inset: 0;
    background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, transparent 50%);
    pointer-events: none;
}
.cc-chip { width: 36px; height: 28px; border-radius: 5px; background: linear-gradient(135deg, #d4a947, #b8942a); opacity: 0.9; }
.cc-bank { font-size: 1.1rem; font-weight: 800; letter-spacing: 0.5px; }
.cc-number { font-size: 0.85rem; font-weight: 600; letter-spacing: 2px; opacity: 0.8; }
.cc-label { font-size: 0.55rem; text-transform: uppercase; opacity: 0.6; letter-spacing: 1px; }
.cc-value { font-size: 0.8rem; font-weight: 700; }

/* ═══════════════════════════════════════════════════════════════════
   TOOLTIP HELPER (didactic)
   ═══════════════════════════════════════════════════════════════════ */
.tooltip-help {
    display: inline-flex; align-items: center; justify-content: center;
    width: 16px; height: 16px;
    border-radius: 50%;
    background: rgba(78,140,255,0.15);
    color: var(--blue);
    font-size: 0.55rem; font-weight: 800;
    cursor: help;
    position: relative;
    vertical-align: middle;
    margin-left: 0.3rem;
    transition: all 0.2s;
}
.tooltip-help:hover { background: rgba(78,140,255,0.3); transform: scale(1.15); }
.tooltip-help .tooltip-content {
    display: none;
    position: absolute;
    bottom: calc(100% + 8px);
    left: 50%;
    transform: translateX(-50%);
    background: var(--card-solid);
    border: 1px solid var(--border-light);
    border-radius: var(--radius-sm);
    padding: 0.6rem 0.8rem;
    font-size: 0.72rem;
    color: var(--text);
    font-weight: 400;
    line-height: 1.5;
    white-space: normal;
    width: 220px;
    z-index: 100;
    box-shadow: var(--shadow-lg);
}
.tooltip-help:hover .tooltip-content { display: block; animation: fadeInUp 0.2s var(--ease-smooth); }

/* ═══════════════════════════════════════════════════════════════════
   EMPTY STATE
   ═══════════════════════════════════════════════════════════════════ */
.empty-state {
    text-align: center;
    padding: 3rem 2rem;
    animation: fadeInUp 0.6s var(--ease-smooth);
}
.empty-state .empty-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
    animation: float 3s ease-in-out infinite;
}
.empty-state .empty-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 0.5rem;
}
.empty-state .empty-desc {
    font-size: 0.82rem;
    color: var(--text2);
    line-height: 1.6;
    max-width: 400px;
    margin: 0 auto 1.2rem;
}
.empty-state .empty-cta {
    display: inline-flex; align-items: center; gap: 0.4rem;
    padding: 0.6rem 1.2rem;
    background: linear-gradient(135deg, var(--green), var(--green-dim));
    color: var(--bg);
    border-radius: 10px;
    font-size: 0.82rem;
    font-weight: 700;
    text-decoration: none;
    transition: all 0.3s;
    box-shadow: 0 4px 15px rgba(0,212,170,0.25);
}
.empty-state .empty-cta:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(0,212,170,0.35); }

/* ═══════════════════════════════════════════════════════════════════
   ONBOARDING WIZARD
   ═══════════════════════════════════════════════════════════════════ */
.onboarding-card {
    background: linear-gradient(135deg, rgba(78,140,255,0.08), rgba(0,212,170,0.06));
    border: 1px solid rgba(78,140,255,0.15);
    border-radius: var(--radius-xl);
    padding: 2rem;
    margin-bottom: 1.5rem;
    animation: fadeInUp 0.6s var(--ease-smooth);
    position: relative;
    overflow: hidden;
}
.onboarding-card::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--green), var(--blue));
}
.onboarding-step {
    display: flex; align-items: center; gap: 1rem;
    padding: 0.8rem 1rem;
    border-radius: var(--radius-md);
    margin-bottom: 0.5rem;
    transition: all 0.3s;
    border: 1px solid transparent;
}
.onboarding-step:hover { background: rgba(255,255,255,0.03); border-color: var(--border); }
.onboarding-step .step-number {
    width: 32px; height: 32px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.75rem; font-weight: 800;
    flex-shrink: 0;
}
.onboarding-step .step-number.pending { background: rgba(255,255,255,0.06); color: var(--text3); border: 2px solid var(--border); }
.onboarding-step .step-number.done { background: var(--green); color: var(--bg); }
.onboarding-step .step-title { font-size: 0.88rem; font-weight: 600; color: var(--text); }
.onboarding-step .step-desc { font-size: 0.72rem; color: var(--text2); }
.onboarding-progress {
    height: 4px;
    border-radius: 4px;
    background: rgba(255,255,255,0.06);
    margin-top: 1rem;
    overflow: hidden;
}
.onboarding-progress-fill {
    height: 100%;
    border-radius: 4px;
    background: linear-gradient(90deg, var(--green), var(--blue));
    transition: width 0.8s var(--ease-smooth);
}

/* ═══════════════════════════════════════════════════════════════════
   SIDEBAR
   ═══════════════════════════════════════════════════════════════════ */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1017 0%, #0a0d13 100%) !important;
}
[data-testid="stSidebar"] .stButton > button {
    width: 100%;
    background: linear-gradient(135deg, #00d4aa, #00a888) !important;
    color: #0b0e14 !important;
    border: none !important;
    border-radius: var(--radius-md) !important;
    padding: 0.65rem 1rem !important;
    font-weight: 700 !important;
    font-size: 0.82rem !important;
    letter-spacing: 0.3px !important;
    transition: all 0.3s var(--ease-smooth) !important;
    box-shadow: 0 4px 15px rgba(0,212,170,0.2) !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(0,212,170,0.35) !important;
}

/* Sidebar toggle button */
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"] {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    visibility: visible !important;
    opacity: 1 !important;
    z-index: 999999 !important;
    position: fixed !important;
    top: 0.5rem !important;
    left: 0.5rem !important;
    background: var(--green-glow) !important;
    border: 2px solid var(--green) !important;
    border-radius: 10px !important;
    padding: 0.5rem !important;
    transition: all 0.3s var(--ease-smooth) !important;
    box-shadow: var(--shadow-glow-green) !important;
    cursor: pointer !important;
}
[data-testid="collapsedControl"]:hover,
[data-testid="stSidebarCollapsedControl"]:hover {
    background: var(--green) !important;
    box-shadow: 0 4px 20px rgba(0,212,170,0.6) !important;
    transform: scale(1.05) !important;
}
[data-testid="collapsedControl"] svg,
[data-testid="stSidebarCollapsedControl"] svg {
    fill: #ffffff !important; color: #ffffff !important;
    width: 24px !important; height: 24px !important;
}

.sidebar-brand { text-align: center; padding: 0.5rem 0 1rem 0; }
.sidebar-brand h2 { font-size: 1.3rem; font-weight: 800; margin: 0; }
.sidebar-brand h2 span {
    background: linear-gradient(135deg, var(--green) 0%, var(--blue) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.sidebar-brand p {
    font-size: 0.72rem; color: var(--text3);
    margin: 0.1rem 0 0 0; letter-spacing: 1px; text-transform: uppercase;
}

.sidebar-stat {
    background: rgba(255,255,255,0.03);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    padding: 0.7rem 0.9rem;
    margin-bottom: 0.35rem;
    display: flex; justify-content: space-between; align-items: center;
    transition: all 0.25s var(--ease-smooth);
}
.sidebar-stat:hover { background: rgba(255,255,255,0.05); border-color: var(--border-light); }
.sidebar-stat .ss-label { font-size: 0.7rem; color: var(--text2); font-weight: 500; }
.sidebar-stat .ss-value { font-size: 0.88rem; font-weight: 700; }

/* ═══════════════════════════════════════════════════════════════════
   NAVIGATION PILLS (TABS)
   ═══════════════════════════════════════════════════════════════════ */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.2rem;
    border-bottom: 1px solid var(--border);
    padding-bottom: 0;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 10px 10px 0 0;
    font-weight: 500;
    font-size: 0.78rem;
    padding: 0.4rem 0.6rem;
}

/* Streamlit pills widget styling */
[data-testid="stPills"] button {
    transition: all 0.3s var(--ease-smooth) !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 0.78rem !important;
    border: 1px solid var(--border) !important;
}
[data-testid="stPills"] button:hover {
    transform: translateY(-1px) !important;
    border-color: var(--border-light) !important;
    box-shadow: var(--shadow-sm) !important;
}
[data-testid="stPills"] button[aria-checked="true"] {
    background: linear-gradient(135deg, var(--green), var(--green-dim)) !important;
    color: var(--bg) !important;
    border-color: var(--green) !important;
    box-shadow: var(--shadow-glow-green) !important;
    font-weight: 700 !important;
}

/* ═══════════════════════════════════════════════════════════════════
   FORM STYLING
   ═══════════════════════════════════════════════════════════════════ */
[data-testid="stForm"] {
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-lg) !important;
    padding: 1.2rem !important;
    background: var(--card) !important;
}

/* ═══════════════════════════════════════════════════════════════════
   SKELETON LOADING
   ═══════════════════════════════════════════════════════════════════ */
.skeleton {
    background: linear-gradient(90deg,
        rgba(255,255,255,0.04) 25%,
        rgba(255,255,255,0.08) 50%,
        rgba(255,255,255,0.04) 75%
    );
    background-size: 200% 100%;
    animation: shimmerLoad 1.5s infinite;
    border-radius: var(--radius-sm);
}
.skeleton-text { height: 12px; margin-bottom: 8px; }
.skeleton-value { height: 28px; width: 60%; margin-bottom: 8px; }
.skeleton-chart { height: 200px; }

/* ═══════════════════════════════════════════════════════════════════
   GLOSSARY
   ═══════════════════════════════════════════════════════════════════ */
.glossary-term {
    padding: 0.8rem 1rem;
    border-bottom: 1px solid var(--border);
    transition: background 0.2s;
}
.glossary-term:hover { background: rgba(255,255,255,0.02); }
.glossary-term:last-child { border-bottom: none; }
.glossary-word { font-size: 0.88rem; font-weight: 700; color: var(--green); margin-bottom: 0.2rem; }
.glossary-def { font-size: 0.78rem; color: var(--text2); line-height: 1.5; }

/* ═══════════════════════════════════════════════════════════════════
   GAMIFICATION (Badges, Streaks, etc)
   ═══════════════════════════════════════════════════════════════════ */
.badge-card {
    background: var(--card);
    border: 1px solid var(--border);
    padding: 1rem;
    border-radius: var(--radius-md);
    text-align: center;
    position: relative;
    overflow: hidden;
    transition: all 0.3s var(--ease-smooth);
    animation: scaleIn 0.5s var(--ease-smooth) forwards;
}
.badge-card:hover { transform: translateY(-3px); box-shadow: var(--shadow-md); }
.badge-card .badge-glow {
    position: absolute; top: -10px; right: -10px;
    width: 50px; height: 50px;
    filter: blur(25px);
    opacity: 0.25;
    border-radius: 50%;
    pointer-events: none;
}
.badge-emoji { font-size: 2.2rem; margin-bottom: 0.4rem; }
.badge-title { font-weight: 700; font-size: 0.88rem; margin-bottom: 0.15rem; }
.badge-desc { font-size: 0.68rem; color: var(--text2); }

.streak-bar {
    display: flex; align-items: center; gap: 0.5rem;
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    padding: 0.7rem 1rem;
    margin-bottom: 0.8rem;
}
.streak-fire { font-size: 1.5rem; animation: float 2s ease-in-out infinite; }
.streak-count { font-size: 1.3rem; font-weight: 900; color: var(--amber); }
.streak-label { font-size: 0.72rem; color: var(--text2); }

/* ═══════════════════════════════════════════════════════════════════
   MEDIA QUERIES (Responsive)
   ═══════════════════════════════════════════════════════════════════ */
@media (max-width: 768px) {
    .glass-card, .metric-card { padding: 1rem; }
    .metric-value { font-size: 1.15rem; }
    .hero-value { font-size: 1.8rem; }
    .app-header { padding: 1.2rem; }
    .app-header h1 { font-size: 1.3rem; }
    .credit-card-visual { max-width: 280px; }
    .cal-day { font-size: 0.55rem; }
    .cal-day .cal-amount { display: none; }
    .hero-card { padding: 1.4rem; }
    .onboarding-card { padding: 1.2rem; }
}

@media (max-width: 480px) {
    .hero-value { font-size: 1.5rem; }
    .metric-value { font-size: 1rem; }
    .activity-feed { padding-left: 0.8rem; }
}
</style>
""", unsafe_allow_html=True)

    # ── Injeção de tags PWA (Fase 1.1) ──
    st.html("""
    <script>
    // Acessa o head do documento principal
    const head = document.head || window.parent.document.head;
    if (head && !head.querySelector('meta[name="apple-mobile-web-app-capable"]')) {
        head.insertAdjacentHTML('beforeend', '<meta name="apple-mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-status-bar-style" content="black-translucent"><meta name="theme-color" content="#0b0e14"><link rel="apple-touch-icon" href="https://cdn-icons-png.flaticon.com/512/3135/3135715.png">');
    }
    </script>
    """)
