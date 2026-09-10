"""
components/tooltip_helper.py — Componente de tooltips contextuais para explicar conceitos financeiros.
"""

# Dicionário de explicações de conceitos financeiros em PT-BR
EXPLICACOES = {
    "balanco": "O Balanço Líquido mostra o quanto sobrou (ou faltou) depois de subtrair todas as despesas e o imposto Simples Nacional da sua receita total do mês.",
    "simples": "O Simples Nacional é um regime tributário para pequenas empresas e MEIs. A alíquota de 6% é a faixa inicial, aplicada sobre o faturamento bruto mensal.",
    "receita": "Receitas são todos os valores que você recebeu no mês: salário, freelances, vendas, rendimentos de investimentos, etc.",
    "despesa": "Despesas são todos os gastos do mês: contas fixas (aluguel, internet), variáveis (alimentação, transporte) e eventuais.",
    "saldo": "O Saldo é o valor disponível na sua conta depois de somar tudo que entrou e subtrair tudo que saiu, partindo do saldo inicial.",
    "reserva": "A Reserva de Emergência é um dinheiro guardado para imprevistos (demissão, doença, conserto). O ideal é ter entre 6 a 12 meses do seu custo mensal.",
    "score": "O Score de Saúde Financeira é uma nota de 0 a 100 que avalia vários aspectos: proporção receita/despesa, reserva, investimentos, controle de orçamento, etc.",
    "regra503020": "A Regra 50-30-20 sugere dividir sua renda em: 50% para necessidades (moradia, contas), 30% para desejos (lazer, compras) e 20% para prioridades (investimentos, dívidas).",
    "cdi": "CDI (Certificado de Depósito Interbancário) é a taxa de juros que os bancos cobram entre si. Ela serve de referência para rendimentos de CDBs, LCIs e outros investimentos.",
    "selic": "A Taxa Selic é a taxa básica de juros do Brasil, definida pelo Banco Central. Quando ela sobe, investimentos de renda fixa rendem mais, mas empréstimos ficam mais caros.",
    "ipca": "IPCA é o Índice de Preços ao Consumidor Amplo — basicamente, a inflação oficial do Brasil. Ele mede quanto os preços subiram em um período.",
    "fgc": "O FGC (Fundo Garantidor de Créditos) protege seu dinheiro em bancos. Se o banco quebrar, o FGC devolve até R$ 250 mil por CPF por instituição.",
    "tesouro_selic": "O Tesouro Selic é um título público do governo que rende a Taxa Selic. É o investimento mais seguro do Brasil, com resgate em D+1 (um dia útil).",
    "cdb": "CDB (Certificado de Depósito Bancário) é um empréstimo que você faz ao banco. Em troca, ele te paga juros. Pode ser de liquidez diária ou com prazo fixo.",
    "lci_lca": "LCI (Letra de Crédito Imobiliário) e LCA (Letra de Crédito do Agronegócio) são investimentos isentos de Imposto de Renda para pessoa física.",
    "ir_regressivo": "O IR Regressivo é a tabela de imposto sobre investimentos: 22,5% (até 180 dias), 20% (181-360), 17,5% (361-720), 15% (acima de 720 dias). Quanto mais tempo, menos imposto.",
    "base_zero": "Orçamento Base Zero significa alocar 100% da sua renda em categorias específicas (potes), para que cada real tenha um destino. Nada fica 'sem nome'.",
    "recorrente": "Transações recorrentes são gastos fixos que se repetem todo mês automaticamente: aluguel, internet, streaming, seguro, etc.",
    "patrimonio": "Patrimônio Líquido é a soma de tudo que você tem (contas, investimentos, reserva) menos suas dívidas. Representa sua riqueza real.",
}


def get_tooltip(key):
    """Retorna HTML de tooltip para uma chave do dicionário."""
    text = EXPLICACOES.get(key, "")
    if not text:
        return ""
    return (
        f'<span class="tooltip-help">?'
        f'<span class="tooltip-content">{text}</span>'
        f'</span>'
    )


def render_tooltip_inline(label, key):
    """Retorna label + tooltip inline para uso em HTML."""
    tip = get_tooltip(key)
    return f'{label}{tip}'
