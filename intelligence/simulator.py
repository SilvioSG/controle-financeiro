"""
intelligence/simulator.py — Simulador de investimentos com juros compostos.
"""


def simular_investimento(capital, aporte_mensal, meses, taxa_anual):
    """Simula investimento com juros compostos e IR regressivo."""
    taxa_mensal = (1 + taxa_anual / 100) ** (1 / 12) - 1
    historico = []
    saldo = capital
    total_investido = capital

    for m in range(1, meses + 1):
        saldo = saldo * (1 + taxa_mensal) + aporte_mensal
        total_investido += aporte_mensal
        historico.append({"mes": m, "saldo": saldo, "investido": total_investido})

    rendimento_bruto = saldo - total_investido

    # IR regressivo
    if meses <= 6:
        aliq = 0.225
    elif meses <= 12:
        aliq = 0.20
    elif meses <= 24:
        aliq = 0.175
    else:
        aliq = 0.15

    ir = rendimento_bruto * aliq
    saldo_liquido = saldo - ir

    return {
        "bruto": saldo,
        "investido": total_investido,
        "rendimento": rendimento_bruto,
        "ir": ir,
        "aliquota": aliq * 100,
        "liquido": saldo_liquido,
        "historico": historico,
    }
