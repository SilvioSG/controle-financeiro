"""
core/utils.py — Formatação, constantes e helpers compartilhados.
"""
from datetime import datetime, date, timedelta

# ─── Constantes ───────────────────────────────────────────────────────────────

TAXA_SIMPLES = 0.06

MESES_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro",
}

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color="#8b95a5", size=12),
    margin=dict(l=25, r=25, t=40, b=25),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#8b95a5", size=11)),
)


# ─── Funções de Formatação ────────────────────────────────────────────────────

def fmt(v):
    """Formata valor em Real brasileiro: R$ 1.234,56"""
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_data_pt(d):
    """Formata data para exibição: 'Hoje', 'Ontem' ou 'DD/MM/YYYY'."""
    try:
        dt = datetime.strptime(d, "%Y-%m-%d")
        h = date.today()
        if dt.date() == h:
            return "Hoje"
        elif dt.date() == h - timedelta(days=1):
            return "Ontem"
        else:
            return dt.strftime("%d/%m/%Y")
    except Exception:
        return d


def get_pref(m, a):
    """Retorna (prefixo 'YYYY-MM', mês ajustado, ano ajustado) para meses negativos."""
    while m <= 0:
        m += 12
        a -= 1
    return f"{a}-{m:02d}", m, a
