"""
intelligence/categorizer.py — Categorização automática por descrição (Fase 4.1).
"""

# Mapeamento padrão de palavras-chave para categorias
DEFAULT_MAPPINGS = {
    # Alimentação
    "supermercado": "Alimentação", "mercado": "Alimentação", "padaria": "Alimentação",
    "restaurante": "Alimentação", "lanchonete": "Alimentação", "ifood": "Alimentação",
    "rappi": "Alimentação", "uber eats": "Alimentação", "açougue": "Alimentação",
    "hortifruti": "Alimentação", "café": "Alimentação", "almoço": "Alimentação",
    "jantar": "Alimentação", "pizza": "Alimentação", "hambúrguer": "Alimentação",
    "pão": "Alimentação", "feira": "Alimentação",
    # Transporte
    "uber": "Transporte", "99": "Transporte", "combustível": "Transporte",
    "gasolina": "Transporte", "álcool": "Transporte", "estacionamento": "Transporte",
    "pedágio": "Transporte", "ônibus": "Transporte", "metrô": "Transporte",
    "passagem": "Transporte", "bilhete": "Transporte",
    # Saúde
    "farmácia": "Saúde", "drogaria": "Saúde", "médico": "Saúde",
    "consulta": "Saúde", "exame": "Saúde", "hospital": "Saúde",
    "dentista": "Saúde", "plano de saúde": "Saúde",
    # Assinaturas
    "netflix": "Assinaturas", "spotify": "Assinaturas", "disney": "Assinaturas",
    "amazon prime": "Assinaturas", "hbo": "Assinaturas", "youtube": "Assinaturas",
    "globoplay": "Assinaturas", "internet": "Assinaturas", "celular": "Assinaturas",
    # Moradia
    "aluguel": "Moradia", "condomínio": "Moradia", "luz": "Moradia",
    "energia": "Moradia", "água": "Moradia", "gás": "Moradia", "iptu": "Moradia",
    # Educação
    "faculdade": "Educação", "curso": "Educação", "escola": "Educação",
    "livro": "Educação", "udemy": "Educação", "alura": "Educação",
    # Lazer
    "cinema": "Lazer", "show": "Lazer", "viagem": "Lazer", "hotel": "Lazer",
    "bar": "Lazer", "festa": "Lazer", "ingresso": "Lazer",
    # Roupas
    "roupa": "Roupas", "calçado": "Roupas", "tênis": "Roupas",
    "camiseta": "Roupas", "renner": "Roupas", "c&a": "Roupas",
    # Receitas
    "salário": "Salário", "freelance": "Freelance", "dividendo": "Investimentos",
    "rendimento": "Investimentos", "pix recebido": "Outros (Receita)",
}


def sugerir_categoria(conn, descricao):
    """
    Sugere uma categoria baseada na descrição.
    Primeiro verifica mapeamentos do usuário no banco, depois usa os padrões.
    Retorna (categoria_id, nome_categoria) ou (None, None).
    """
    desc_lower = descricao.lower().strip()

    # 1. Verificar mapeamentos personalizados do banco
    mappings_db = conn.execute(
        "SELECT palavra, categoria_id FROM mapeamento_categorias"
    ).fetchall()
    for palavra, cat_id in mappings_db:
        if palavra.lower() in desc_lower:
            cat = conn.execute("SELECT id, nome FROM categorias WHERE id=?", (cat_id,)).fetchone()
            if cat:
                return cat[0], cat[1]

    # 2. Usar mapeamento padrão
    for palavra, cat_nome in DEFAULT_MAPPINGS.items():
        if palavra in desc_lower:
            cat = conn.execute("SELECT id, nome FROM categorias WHERE nome=?", (cat_nome,)).fetchone()
            if cat:
                return cat[0], cat[1]

    return None, None


def aprender_categoria(conn, descricao, categoria_id):
    """Salva o mapeamento para aprender com o usuário."""
    palavras = descricao.lower().strip().split()
    # Usar a palavra mais longa da descrição (geralmente é a mais significativa)
    if palavras:
        palavra_chave = max(palavras, key=len)
        if len(palavra_chave) >= 3:
            conn.execute(
                "INSERT OR REPLACE INTO mapeamento_categorias (palavra, categoria_id) VALUES (?,?)",
                (palavra_chave, categoria_id),
            )
            conn.commit()
