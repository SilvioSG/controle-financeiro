"""
intelligence/simulator.py — Simulador de investimentos com juros compostos e desconto de inflação.
"""


def simular_investimento(capital, aporte_mensal, meses, taxa_anual, inflacao_anual=0.0, isento_ir=False):
    """Simula investimento com juros compostos, IR regressivo e poder de compra real (descontando inflação)."""
    taxa_mensal = (1 + taxa_anual / 100) ** (1 / 12) - 1
    inflacao_mensal = (1 + inflacao_anual / 100) ** (1 / 12) - 1 if inflacao_anual > 0 else 0.0

    historico = []
    saldo = capital
    total_investido = capital

    for m in range(1, meses + 1):
        saldo = saldo * (1 + taxa_mensal) + aporte_mensal
        total_investido += aporte_mensal
        fator_inflacao = (1 + inflacao_mensal) ** m
        saldo_real_mes = saldo / fator_inflacao if fator_inflacao > 0 else saldo
        historico.append({
            "mes": m,
            "saldo": saldo,
            "saldo_real": saldo_real_mes,
            "investido": total_investido,
        })

    rendimento_bruto = saldo - total_investido

    # IR regressivo
    if isento_ir:
        aliq = 0.0
    elif meses <= 6:
        aliq = 0.225
    elif meses <= 12:
        aliq = 0.20
    elif meses <= 24:
        aliq = 0.175
    else:
        aliq = 0.15

    ir = rendimento_bruto * aliq
    saldo_liquido = saldo - ir
    fator_inflacao_final = (1 + inflacao_mensal) ** meses
    liquido_real = saldo_liquido / fator_inflacao_final if fator_inflacao_final > 0 else saldo_liquido

    return {
        "bruto": saldo,
        "investido": total_investido,
        "rendimento": rendimento_bruto,
        "ir": ir,
        "aliquota": aliq * 100,
        "liquido": saldo_liquido,
        "liquido_real": liquido_real,
        "historico": historico,
    }
