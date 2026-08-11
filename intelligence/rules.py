"""
intelligence/rules.py — Regra 50-30-20 e classificação de categorias.
"""

# Categorias mapeadas para regra 50-30-20
NECESSIDADES = {"Alimentação", "Transporte", "Moradia", "Saúde", "Educação", "Cartão"}
DESEJOS = {"Lazer", "Roupas", "Assinaturas", "Compras", "Outros (Despesa)"}


def calcular_50_30_20(conn, prefixo, rec):
    """Calcula distribuição real vs ideal pela regra 50-30-20."""
    gastos_cat = conn.execute("""
        SELECT c.nome, SUM(t.valor) as total FROM transacoes t
        JOIN categorias c ON t.categoria_id = c.id
        WHERE t.tipo='despesa' AND t.data LIKE ?
        GROUP BY c.id
    """, (f"{prefixo}%",)).fetchall()

    nec, des, pri = 0, 0, 0
    for nome, total in gastos_cat:
        if nome in NECESSIDADES:
            nec += total
        elif nome in DESEJOS:
            des += total
        else:
            pri += total  # Outras categorias vão para prioridades

    return {
        "necessidades": {"valor": nec, "pct": (nec / rec * 100) if rec > 0 else 0, "ideal": 50},
        "desejos": {"valor": des, "pct": (des / rec * 100) if rec > 0 else 0, "ideal": 30},
        "prioridades": {"valor": pri, "pct": (pri / rec * 100) if rec > 0 else 0, "ideal": 20},
    }
