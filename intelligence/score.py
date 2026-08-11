"""
intelligence/score.py — Cálculo do score de saúde financeira (0-100).
"""
from core.utils import get_pref
from core.database import saldo_conta


def calcular_score(conn, rec, desp, simples, prefixo, mes, ano, saldo_reserva=0):
    """Score de saúde financeira 0-100."""
    pontos = 0

    # 1. Taxa de poupança (30 pts) — (rec - desp - simples) / rec
    if rec > 0:
        taxa = (rec - desp - simples) / rec
        pontos += min(taxa / 0.20, 1.0) * 30
    elif desp == 0:
        pontos += 15  # sem dados

    # 2. Reserva de emergência (25 pts)
    metas = conn.execute("SELECT valor_meta, valor_atual FROM metas").fetchall()
    pontos_reserva = 0
    if metas:
        best_meta = max((a / m if m > 0 else 0) for m, a in metas)
        pontos_reserva = min(best_meta, 1.0) * 25

    if saldo_reserva > 0 and desp > 0:
        meses_garantidos = saldo_reserva / desp
        pontos_conta = min(meses_garantidos / 6, 1.0) * 25
        pontos_reserva = max(pontos_reserva, pontos_conta)

    pontos += pontos_reserva

    # 3. Orçamento sob controle (20 pts)
    orcs = conn.execute(
        "SELECT o.categoria_id, o.valor_limite FROM orcamentos o WHERE o.mes=? AND o.ano=?",
        (mes, ano),
    ).fetchall()
    if orcs:
        # Pega gastos de todas as categorias no mês em 1 query (evita N+1)
        g_por_cat = conn.execute(
            "SELECT categoria_id, SUM(valor) FROM transacoes WHERE tipo='despesa' AND data LIKE ? GROUP BY categoria_id",
            (f"{prefixo}%",)
        ).fetchall()
        gastos_dict = {row[0]: row[1] for row in g_por_cat}
        
        dentro = sum(1 for cat_id, lim in orcs if gastos_dict.get(cat_id, 0) <= lim)
        pontos += (dentro / len(orcs)) * 20
    else:
        pontos += 10  # sem orçamento = neutro

    # 4. Tendência de gastos (15 pts) — comparar últimos 3 meses (1 query unificada)
    prefs = [get_pref(mes - i, ano)[0] for i in range(1, 4)]
    conds = " OR ".join(["data LIKE ?"] * 3)
    params = tuple(f"{p}%" for p in prefs)
    g_3m_data = conn.execute(
        f"SELECT SUBSTR(data, 1, 7), SUM(valor) FROM transacoes WHERE tipo='despesa' AND ({conds}) GROUP BY SUBSTR(data, 1, 7)",
        params
    ).fetchall()
    gastos_dict_3m = {r[0]: r[1] for r in g_3m_data}
    gastos_3m = [gastos_dict_3m.get(p, 0) for p in prefs]

    if gastos_3m[0] > 0 and desp > 0:
        media = sum(gastos_3m) / len(gastos_3m) if any(gastos_3m) else desp
        if media > 0:
            ratio = desp / media
            if ratio <= 0.9:
                pontos += 15
            elif ratio <= 1.0:
                pontos += 12
            elif ratio <= 1.1:
                pontos += 8
            else:
                pontos += 3
    else:
        pontos += 8

    # 5. Diversificação de receitas (10 pts)
    fontes = conn.execute(
        "SELECT COUNT(DISTINCT categoria_id) FROM transacoes WHERE tipo='receita' AND data LIKE ?",
        (f"{prefixo}%",),
    ).fetchone()[0]
    if fontes >= 3:
        pontos += 10
    elif fontes == 2:
        pontos += 7
    elif fontes == 1:
        pontos += 4

    return min(round(pontos), 100)
