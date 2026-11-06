"""
core/utils.py — Formatação, constantes e helpers compartilhados.
"""
from datetime import datetime, date, timedelta
import json
import urllib.request
import streamlit as st

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


def get_taxa_simples() -> float:
    """Retorna a alíquota configurada pelo usuário (padrão 6% = 0.06)."""
    if "taxa_simples_pct" in st.session_state:
        return float(st.session_state["taxa_simples_pct"]) / 100.0
    try:
        if "tax" in st.secrets and "simples_pct" in st.secrets["tax"]:
            return float(st.secrets["tax"]["simples_pct"]) / 100.0
    except Exception:
        pass
    return TAXA_SIMPLES


def get_gemini_api_key() -> str:
    """Busca a chave da API Gemini em st.secrets ou na sessão atual."""
    if st.session_state.get("gemini_api_key_shared"):
        return st.session_state["gemini_api_key_shared"]
    try:
        if "gemini" in st.secrets and "api_key" in st.secrets["gemini"]:
            return str(st.secrets["gemini"]["api_key"]).strip()
        if "GEMINI_API_KEY" in st.secrets:
            return str(st.secrets["GEMINI_API_KEY"]).strip()
    except Exception:
        pass
    return ""


@st.cache_data(ttl=86400, show_spinner=False)
def get_taxas_bcb() -> dict:
    """Busca taxas Selic, CDI e IPCA (12m) atualizadas na API do Banco Central do Brasil."""
    taxas = {"selic": 14.25, "cdi": 14.15, "ipca": 4.50, "online": False}
    try:
        # Série 432: Meta Selic (% a.a.)
        req_selic = urllib.request.Request(
            "https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1?formato=json",
            headers={"User-Agent": "Mozilla/5.0"},
        )
        with urllib.request.urlopen(req_selic, timeout=2.5) as resp:
            dados = json.loads(resp.read().decode("utf-8"))
            if dados and "valor" in dados[0]:
                selic_val = float(dados[0]["valor"])
                taxas["selic"] = selic_val
                taxas["cdi"] = round(max(0.0, selic_val - 0.10), 2)
                taxas["online"] = True

        # Série 13522: IPCA acumulado 12 meses (%)
        req_ipca = urllib.request.Request(
            "https://api.bcb.gov.br/dados/serie/bcdata.sgs.13522/dados/ultimos/1?formato=json",
            headers={"User-Agent": "Mozilla/5.0"},
        )
        with urllib.request.urlopen(req_ipca, timeout=2.5) as resp:
            dados_ipca = json.loads(resp.read().decode("utf-8"))
            if dados_ipca and "valor" in dados_ipca[0]:
                taxas["ipca"] = float(dados_ipca[0]["valor"])
    except Exception:
        pass
    return taxas


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
    """Retorna (prefixo 'YYYY-MM', mês ajustado, ano ajustado) para meses fora do intervalo 1-12."""
    while m <= 0:
        m += 12
        a -= 1
    while m > 12:
        m -= 12
        a += 1
    return f"{a}-{m:02d}", m, a


def processar_tags(conn, transacao_id, tags_str):
    """Processa string de tags separadas por vírgula: cria tags e associa à transação."""
    tags = [t.strip().lower() for t in tags_str.split(",") if t.strip()]
    for tag_nome in tags:
        # Buscar ou criar a tag
        existing = conn.execute("SELECT id FROM tags WHERE nome = ?", (tag_nome,)).fetchone()
        if existing:
            tag_id = existing[0]
        else:
            if getattr(conn, 'is_postgres', False):
                tag_id = conn.execute(
                    "INSERT INTO tags (nome) VALUES (?) RETURNING id", (tag_nome,)
                ).fetchone()[0]
            else:
                cur = conn.execute("INSERT INTO tags (nome) VALUES (?)", (tag_nome,))
                tag_id = cur.lastrowid

        # Associar tag à transação (ignorar se já existir)
        try:
            if getattr(conn, 'is_postgres', False):
                conn.execute(
                    "INSERT INTO transacao_tags (transacao_id, tag_id) VALUES (?,?) ON CONFLICT DO NOTHING",
                    (transacao_id, tag_id),
                )
            else:
                conn.execute(
                    "INSERT OR IGNORE INTO transacao_tags (transacao_id, tag_id) VALUES (?,?)",
                    (transacao_id, tag_id),
                )
        except Exception:
            pass
