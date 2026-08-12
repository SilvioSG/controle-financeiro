"""
components/styles.py — CSS premium do dashboard financeiro.
"""
import streamlit as st


def inject_css():
    """Injeta o CSS completo do tema premium dark."""
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
:root {
    --bg: #0b0e14; --card: rgba(22,27,38,0.85); --card-solid: #161b26;
    --card-hover: rgba(30,36,50,0.95); --glass: rgba(255,255,255,0.03);
    --border: rgba(255,255,255,0.06); --border-light: rgba(255,255,255,0.10);
    --green: #00d4aa; --green-dim: #00a888; --green-glow: rgba(0,212,170,0.15);
    --red: #ff4b6e; --red-glow: rgba(255,75,110,0.15);
    --blue: #4e8cff; --blue-glow: rgba(78,140,255,0.15);
    --purple: #a855f7; --purple-glow: rgba(168,85,247,0.15);
    --amber: #f59e0b; --amber-glow: rgba(245,158,11,0.15);
    --text: #f0f2f5; --text2: #8b95a5; --text3: #5a6478;
}
html, body { font-family: 'Inter', -apple-system, sans-serif !important; -webkit-font-smoothing: antialiased; }

.glass-card { background: var(--card); backdrop-filter: blur(20px); border: 1px solid var(--border); border-radius: 16px; padding: 1.4rem 1.5rem; transition: all 0.35s cubic-bezier(0.4,0,0.2,1); position: relative; overflow: hidden; }
.glass-card::before { content:''; position: absolute; top:0; left:0; right:0; height:1px; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.08), transparent); }
.glass-card:hover { transform: translateY(-3px); box-shadow: 0 12px 40px rgba(0,0,0,0.4); border-color: var(--border-light); }

.metric-card { background: var(--card); backdrop-filter: blur(20px); border: 1px solid var(--border); border-radius: 16px; padding: 1.2rem 1.3rem; transition: all 0.35s cubic-bezier(0.4,0,0.2,1); position: relative; overflow: hidden; animation: slideUp 0.5s ease-out forwards; }
.metric-card:hover { transform: translateY(-3px); box-shadow: 0 12px 40px rgba(0,0,0,0.4); }
.metric-icon { width: 42px; height: 42px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 1.2rem; margin-bottom: 0.7rem; }
.metric-icon.green { background: linear-gradient(135deg, #00d4aa, #00a888); }
.metric-icon.red { background: linear-gradient(135deg, #ff4b6e, #cc3d58); }
.metric-icon.blue { background: linear-gradient(135deg, #4e8cff, #3a6fd4); }
.metric-icon.amber { background: linear-gradient(135deg, #f59e0b, #d97706); }
.metric-icon.purple { background: linear-gradient(135deg, #a855f7, #8b3fd4); }
.metric-label { font-size: 0.68rem; font-weight: 600; color: var(--text2); text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 0.25rem; }
.metric-value { font-size: 1.45rem; font-weight: 800; margin: 0; line-height: 1.2; }
.metric-badge { display: inline-block; padding: 0.15rem 0.55rem; border-radius: 20px; font-size: 0.62rem; font-weight: 600; margin-top: 0.35rem; letter-spacing: 0.3px; }
.mv-green { color: var(--green); } .mb-green { background: var(--green-glow); color: var(--green); }
.mv-red { color: var(--red); } .mb-red { background: var(--red-glow); color: var(--red); }
.mv-blue { color: var(--blue); } .mb-blue { background: var(--blue-glow); color: var(--blue); }
.mv-amber { color: var(--amber); } .mb-amber { background: var(--amber-glow); color: var(--amber); }
.mv-purple { color: var(--purple); } .mb-purple { background: var(--purple-glow); color: var(--purple); }

.app-header { background: linear-gradient(135deg, var(--card-solid) 0%, rgba(22,27,38,0.6) 100%); backdrop-filter: blur(20px); border: 1px solid var(--border); border-radius: 20px; padding: 1.6rem 2rem; margin-bottom: 1.5rem; position: relative; overflow: hidden; }
.app-header::before { content:''; position: absolute; top:0; left:0; right:0; height:3px; background: linear-gradient(90deg, var(--green), var(--blue), var(--purple), var(--amber)); background-size: 300% 100%; animation: shimmer 4s ease-in-out infinite; }
@keyframes shimmer { 0%,100% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } }
.app-header h1 { font-size: 1.6rem; font-weight: 800; margin: 0 0 0.15rem 0; color: #ffffff !important; }
.app-header p { color: var(--text2); font-size: 0.82rem; margin: 0; font-weight: 400; }

.sec-header { display: flex; align-items: center; gap: 0.6rem; margin: 1.6rem 0 0.9rem 0; }
.sec-header h3 { font-size: 0.95rem; font-weight: 700; color: var(--text); margin: 0; letter-spacing: -0.01em; }
.sec-header .sec-line { flex: 1; height: 1px; background: linear-gradient(90deg, var(--border-light), transparent); }

.tx-item { display: flex; align-items: center; justify-content: space-between; padding: 0.75rem 1.1rem; background: var(--card); border: 1px solid var(--border); border-radius: 12px; margin-bottom: 0.35rem; transition: all 0.25s ease; animation: slideUp 0.4s ease-out forwards; }
.tx-item:hover { background: var(--card-hover); border-color: var(--border-light); transform: translateX(4px); }
.tx-left { display: flex; align-items: center; gap: 0.75rem; }
.tx-cat-icon { width: 38px; height: 38px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 1.1rem; }
.tx-cat-icon.inc-bg { background: var(--green-glow); }
.tx-cat-icon.exp-bg { background: var(--red-glow); }
.tx-desc { font-size: 0.85rem; font-weight: 500; color: var(--text); }
.tx-meta { font-size: 0.7rem; color: var(--text2); margin-top: 1px; }
.tx-amount { font-size: 0.92rem; font-weight: 700; text-align: right; }
.tx-amount.inc { color: var(--green); } .tx-amount.exp { color: var(--red); }
.day-header { font-size: 0.72rem; font-weight: 600; color: var(--text3); text-transform: uppercase; letter-spacing: 0.8px; padding: 0.5rem 0.2rem 0.3rem; border-bottom: 1px solid var(--border); margin-top: 0.8rem; margin-bottom: 0.4rem; }

.account-card { background: var(--card); backdrop-filter: blur(20px); border: 1px solid var(--border); border-radius: 14px; padding: 1.1rem 1.3rem; margin-bottom: 0.5rem; display: flex; align-items: center; justify-content: space-between; transition: all 0.3s ease; animation: slideUp 0.4s ease-out forwards; }
.account-card:hover { background: var(--card-hover); transform: translateX(4px); }
.acc-left { display: flex; align-items: center; gap: 0.8rem; }
.acc-icon-wrap { width: 44px; height: 44px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 1.3rem; background: linear-gradient(135deg, rgba(78,140,255,0.15), rgba(78,140,255,0.05)); }
.acc-name { font-size: 0.9rem; font-weight: 600; color: var(--text); }
.acc-type { font-size: 0.7rem; color: var(--text2); }
.acc-balance { font-size: 1.05rem; font-weight: 700; }

.budget-item { background: var(--card); border: 1px solid var(--border); border-radius: 14px; padding: 1rem 1.3rem; margin-bottom: 0.5rem; animation: slideUp 0.4s ease-out forwards; }
.budget-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem; }
.budget-cat { font-size: 0.85rem; font-weight: 600; color: var(--text); }
.budget-vals { font-size: 0.75rem; color: var(--text2); }
.budget-bar-bg { width: 100%; height: 8px; border-radius: 8px; background: rgba(255,255,255,0.06); overflow: hidden; }
.budget-bar-fill { height: 100%; border-radius: 8px; transition: width 1.2s cubic-bezier(0.4,0,0.2,1); }
.budget-bar-fill.safe { background: linear-gradient(90deg, #00d4aa, #00b894); }
.budget-bar-fill.warn { background: linear-gradient(90deg, #f59e0b, #f97316); }
.budget-bar-fill.over { background: linear-gradient(90deg, #ff4b6e, #ef4444); }

.cat-chip { display: inline-flex; align-items: center; gap: 0.4rem; background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 0.55rem 1rem; margin: 0.2rem; font-size: 0.82rem; color: var(--text); transition: all 0.25s ease; }
.cat-chip:hover { background: var(--card-hover); border-color: var(--border-light); }

.goal-card { background: var(--card); border: 1px solid var(--border); border-radius: 16px; padding: 1.2rem 1.4rem; margin-bottom: 0.6rem; animation: slideUp 0.4s ease-out forwards; }
.goal-bar-bg { width: 100%; height: 10px; border-radius: 10px; background: rgba(255,255,255,0.06); overflow: hidden; margin: 0.5rem 0; }
.goal-bar-fill { height: 100%; border-radius: 10px; transition: width 1.2s cubic-bezier(0.4,0,0.2,1); }
.goal-bar-fill.g-green { background: linear-gradient(90deg, #00d4aa, #00b894); }
.goal-bar-fill.g-amber { background: linear-gradient(90deg, #f59e0b, #f97316); }
.goal-bar-fill.g-red { background: linear-gradient(90deg, #ff4b6e, #ef4444); }

.top-exp { display: flex; align-items: center; justify-content: space-between; padding: 0.55rem 0; border-bottom: 1px solid var(--border); }
.top-exp:last-child { border-bottom: none; }
.top-exp-left { display: flex; align-items: center; gap: 0.6rem; }
.top-exp-rank { width: 22px; height: 22px; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: 0.65rem; font-weight: 700; background: rgba(255,255,255,0.05); color: var(--text2); }
.top-exp-name { font-size: 0.82rem; color: var(--text); font-weight: 500; }
.top-exp-val { font-size: 0.82rem; color: var(--red); font-weight: 700; }

/* Insight cards */
.insight-card { background: var(--card); border: 1px solid var(--border); border-radius: 14px; padding: 1rem 1.2rem; margin-bottom: 0.5rem; display: flex; align-items: flex-start; gap: 0.8rem; animation: slideUp 0.4s ease-out forwards; transition: all 0.25s; }
.insight-card:hover { background: var(--card-hover); transform: translateX(4px); }
.insight-icon { font-size: 1.4rem; flex-shrink: 0; margin-top: 0.1rem; }
.insight-text { font-size: 0.82rem; color: var(--text); line-height: 1.5; }
.insight-text strong { color: var(--green); }
.insight-label { font-size: 0.65rem; color: var(--text3); text-transform: uppercase; letter-spacing: 0.5px; margin-top: 0.3rem; }

/* Rule 50-30-20 bars */
.rule-bar-wrap { margin-bottom: 0.8rem; }
.rule-bar-label { display: flex; justify-content: space-between; margin-bottom: 0.3rem; }
.rule-bar-name { font-size: 0.78rem; font-weight: 600; color: var(--text); }
.rule-bar-vals { font-size: 0.72rem; color: var(--text2); }
.rule-bar-bg { width: 100%; height: 10px; border-radius: 10px; background: rgba(255,255,255,0.06); overflow: hidden; position: relative; }
.rule-bar-fill { height: 100%; border-radius: 10px; transition: width 1s ease; }
.rule-bar-ideal { position: absolute; top: 0; height: 100%; width: 2px; background: #fff; opacity: 0.5; }

/* Sidebar */
[data-testid="stSidebar"] { background: linear-gradient(180deg, #0d1017 0%, #0b0e14 100%) !important; }
[data-testid="stSidebar"] .stButton > button { width: 100%; background: linear-gradient(135deg, #00d4aa, #00a888) !important; color: #0b0e14 !important; border: none !important; border-radius: 12px !important; padding: 0.65rem 1rem !important; font-weight: 700 !important; font-size: 0.82rem !important; letter-spacing: 0.3px !important; transition: all 0.3s ease !important; box-shadow: 0 4px 15px rgba(0,212,170,0.2) !important; }
[data-testid="stSidebar"] .stButton > button:hover { transform: translateY(-2px) !important; box-shadow: 0 8px 25px rgba(0,212,170,0.35) !important; }

/* Sidebar toggle button - always visible and prominent */
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
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 15px rgba(0,212,170,0.4) !important;
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
    fill: #ffffff !important;
    color: #ffffff !important;
    width: 24px !important;
    height: 24px !important;
}
.sidebar-brand { text-align: center; padding: 0.5rem 0 1rem 0; }
.sidebar-brand h2 { font-size: 1.3rem; font-weight: 800; margin: 0; color: #00d4aa !important; }
.sidebar-brand p { font-size: 0.72rem; color: var(--text3); margin: 0.1rem 0 0 0; letter-spacing: 1px; text-transform: uppercase; }
.sidebar-stat { background: rgba(255,255,255,0.03); border: 1px solid var(--border); border-radius: 12px; padding: 0.7rem 0.9rem; margin-bottom: 0.35rem; display: flex; justify-content: space-between; align-items: center; }
.sidebar-stat .ss-label { font-size: 0.7rem; color: var(--text2); font-weight: 500; }
.sidebar-stat .ss-value { font-size: 0.88rem; font-weight: 700; }

.stTabs [data-baseweb="tab-list"] { gap: 0.2rem; border-bottom: 1px solid var(--border); padding-bottom: 0; }
.stTabs [data-baseweb="tab"] { border-radius: 10px 10px 0 0; font-weight: 500; font-size: 0.78rem; padding: 0.4rem 0.6rem; }


@keyframes slideUp { from { opacity: 0; transform: translateY(15px); } to { opacity: 1; transform: translateY(0); } }

/* Media Queries (Fase 5.5) */
@media (max-width: 768px) {
    .glass-card, .metric-card { padding: 1rem; }
    .metric-value { font-size: 1.15rem; }
    .app-header { padding: 1.2rem; }
    .app-header h1 { font-size: 1.3rem; }
    .stAlert > div { border-radius: 12px; }
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
