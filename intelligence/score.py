"""
intelligence/score.py — Cálculo do score de saúde financeira (0-100).
"""
from core.utils import get_pref
from core.database import saldo_conta


def calcular_score(conn, rec, desp, simples, prefixo, mes, ano):
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

    contas_reserva = conn.execute(
        "SELECT id FROM contas WHERE tipo='Reserva de Emergência'"
    ).fetchall()
    saldo_reserva = sum(saldo_conta(conn, c[0]) for c in contas_reserva)
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
        dentro = 0
        for cat_id, lim in orcs:
            g = conn.execute(
                "SELECT COALESCE(SUM(valor),0) FROM transacoes "
                "WHERE tipo='despesa' AND categoria_id=? AND data LIKE ?",
                (cat_id, f"{prefixo}%"),
            ).fetchone()[0]
            if g <= lim:
                dentro += 1
        pontos += (dentro / len(orcs)) * 20
    else:
        pontos += 10  # sem orçamento = neutro

    # 4. Tendência de gastos (15 pts) — comparar últimos 3 meses
    gastos_3m = []
    for i in range(1, 4):
        p, _, _ = get_pref(mes - i, ano)
        g = conn.execute(
            "SELECT COALESCE(SUM(valor),0) FROM transacoes WHERE tipo='despesa' AND data LIKE ?",
            (f"{p}%",),
        ).fetchone()[0]
        gastos_3m.append(g)
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
