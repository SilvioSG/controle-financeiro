"""
intelligence/insights.py — Geração de insights financeiros personalizados.
"""
from core.utils import fmt, get_pref


def gerar_insights(conn, rec, desp, simples, prefixo, mes, ano, saldo_total):
    """Gera lista de insights baseados nos dados reais."""
    tips = []

    # Receita vs Despesa
    if rec > 0:
        pct_gasto = (desp + simples) / rec * 100
        if pct_gasto > 90:
            tips.append((
                "🚨", "Alerta de Gastos",
                f"Seus gastos consomem <strong>{pct_gasto:.0f}%</strong> da renda. "
                f"Tente reduzir para menos de 80%.",
            ))
        elif pct_gasto > 70:
            tips.append((
                "⚠️", "Atenção",
                f"Seus gastos estão em <strong>{pct_gasto:.0f}%</strong> da renda. "
                f"O ideal é até 80%.",
            ))

    # Sobra do mês
    sobra = rec - desp - simples
    if sobra > 0 and rec > 0:
        tips.append((
            "💰", "Oportunidade",
            f"Você tem <strong>{fmt(sobra)}</strong> sobrando. "
            f"Invista em Tesouro Selic ou CDB 100% CDI para fazer seu dinheiro render.",
        ))

    # Sem reserva
    metas = conn.execute("SELECT valor_meta, valor_atual FROM metas").fetchall()
    if not metas and desp > 0:
        reserva_ideal = desp * 6
        tips.append((
            "🛡️", "Reserva de Emergência",
            f"Você não tem metas criadas. Crie uma reserva de "
            f"<strong>{fmt(reserva_ideal)}</strong> (6x suas despesas mensais).",
        ))

    # Orçamentos estourados
    orcs = conn.execute("""
        SELECT c.nome, c.icone, o.valor_limite FROM orcamentos o
        JOIN categorias c ON o.categoria_id = c.id WHERE o.mes=? AND o.ano=?
    """, (mes, ano)).fetchall()
    for nome, icone, lim in orcs:
        cat_id = conn.execute("SELECT id FROM categorias WHERE nome=?", (nome,)).fetchone()
        if cat_id:
            g = conn.execute(
                "SELECT COALESCE(SUM(valor),0) FROM transacoes "
                "WHERE tipo='despesa' AND categoria_id=? AND data LIKE ?",
                (cat_id[0], f"{prefixo}%"),
            ).fetchone()[0]
            if g > lim:
                tips.append((
                    "🚨", f"{icone} {nome}",
                    f"Ultrapassou o limite em <strong>{fmt(g - lim)}</strong> "
                    f"({fmt(g)} / {fmt(lim)}).",
                ))

    # Tendência de gastos
    g_ant_p, _, _ = get_pref(mes - 1, ano)
    g_anterior = conn.execute(
        "SELECT COALESCE(SUM(valor),0) FROM transacoes WHERE tipo='despesa' AND data LIKE ?",
        (f"{g_ant_p}%",),
    ).fetchone()[0]
    if g_anterior > 0 and desp > 0:
        variacao = ((desp - g_anterior) / g_anterior) * 100
        if variacao > 15:
            tips.append((
                "📈", "Gastos Crescendo",
                f"Despesas aumentaram <strong>{variacao:.0f}%</strong> "
                f"em relação ao mês anterior.",
            ))
        elif variacao < -10:
            tips.append((
                "📉", "Parabéns!",
                f"Despesas reduziram <strong>{abs(variacao):.0f}%</strong> "
                f"em relação ao mês anterior. Continue assim!",
            ))

    # Categoria mais cara
    top_cat = conn.execute("""
        SELECT c.nome, c.icone, SUM(t.valor) as total FROM transacoes t
        JOIN categorias c ON t.categoria_id = c.id
        WHERE t.tipo='despesa' AND t.data LIKE ?
        GROUP BY c.id ORDER BY total DESC LIMIT 1
    """, (f"{prefixo}%",)).fetchone()
    if top_cat and rec > 0:
        pct_top = top_cat[2] / rec * 100
        if pct_top > 30:
            tips.append((
                "🔥", "Maior Gasto",
                f"<strong>{top_cat[1]} {top_cat[0]}</strong> consome "
                f"<strong>{pct_top:.0f}%</strong> da sua renda. Avalie se é possível reduzir.",
            ))

    # Dica de investimento
    if saldo_total > 1000:
        tips.append((
            "💹", "Investimento",
            f"Com saldo de <strong>{fmt(saldo_total)}</strong>, considere: "
            f"Tesouro Selic (seguro, ~14% a.a.), CDB 120% CDI (~17% a.a.) ou "
            f"LCI/LCA (isento de IR).",
        ))

    if not tips:
        tips.append(("✨", "Tudo em Ordem", "Continue assim! Suas finanças estão saudáveis."))

    return tips
