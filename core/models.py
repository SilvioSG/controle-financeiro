"""
core/models.py — Funções CRUD organizadas para acesso ao banco de dados.
"""
import pandas as pd
from core.database import read_sql


# ─── Transações ───────────────────────────────────────────────────────────────

def get_receita_mes(conn, prefixo):
    """Retorna total de receitas do mês (prefixo = 'YYYY-MM')."""
    return conn.execute(
        "SELECT COALESCE(SUM(valor),0) FROM transacoes WHERE tipo='receita' AND data LIKE ?",
        (f"{prefixo}%",),
    ).fetchone()[0]


def get_despesa_mes(conn, prefixo):
    """Retorna total de despesas do mês."""
    return conn.execute(
        "SELECT COALESCE(SUM(valor),0) FROM transacoes WHERE tipo='despesa' AND data LIKE ?",
        (f"{prefixo}%",),
    ).fetchone()[0]


def get_transacoes_mes(conn, prefixo, busca=""):
    """Retorna DataFrame de transações do mês com join de categoria e conta."""
    busca_sql = f"%{busca}%" if busca else "%"

    # GROUP_CONCAT (SQLite) vs STRING_AGG (PostgreSQL)
    if getattr(conn, 'is_postgres', False):
        agg_fn = "STRING_AGG(tg.nome, ', ')"
    else:
        agg_fn = "GROUP_CONCAT(tg.nome, ', ')"

    sql = f"""
        SELECT t.id, t.tipo, t.descricao, t.valor, t.data, t.recorrente, t.observacao,
               c.nome as cat, c.icone as ci, co.nome as conta,
               (SELECT {agg_fn} FROM tags tg JOIN transacao_tags tt ON tg.id = tt.tag_id WHERE tt.transacao_id = t.id) as tags_str
        FROM transacoes t
        LEFT JOIN categorias c ON t.categoria_id = c.id
        LEFT JOIN contas co ON t.conta_id = co.id
        WHERE t.data LIKE ? AND t.descricao LIKE ?
        ORDER BY t.data DESC, t.id DESC
        """

    return read_sql(
        sql,
        conn,
        params=(f"{prefixo}%", busca_sql),
    )


def add_transacao(conn, tipo, descricao, valor, data, categoria_id, conta_id, recorrente=0, observacao=""):
    """Insere uma nova transação."""
    conn.execute(
        "INSERT INTO transacoes (tipo, descricao, valor, data, categoria_id, conta_id, recorrente, observacao) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (tipo, descricao, valor, data, categoria_id, conta_id, recorrente, observacao),
    )
    conn.commit()


def update_transacao(conn, tx_id, descricao, valor, data, categoria_id, conta_id, observacao=""):
    """Atualiza uma transação existente."""
    conn.execute(
        "UPDATE transacoes SET descricao=?, valor=?, data=?, categoria_id=?, conta_id=?, observacao=? WHERE id=?",
        (descricao, valor, data, categoria_id, conta_id, observacao, tx_id),
    )
    conn.commit()


def delete_transacao(conn, tx_id):
    """Remove uma transação."""
    conn.execute("DELETE FROM transacoes WHERE id=?", (tx_id,))
    conn.commit()


# ─── Contas ───────────────────────────────────────────────────────────────────

def get_contas(conn):
    """Retorna DataFrame de todas as contas."""
    return read_sql("SELECT * FROM contas", conn)


def get_categorias(conn):
    """Retorna DataFrame de todas as categorias."""
    return read_sql("SELECT id, nome, icone, tipo FROM categorias", conn)


def get_categorias_despesa(conn):
    """Retorna categorias de despesa/ambos."""
    return read_sql(
        "SELECT id, nome, icone FROM categorias WHERE tipo IN ('despesa','ambos') ORDER BY nome",
        conn,
    )


# ─── Orçamento ────────────────────────────────────────────────────────────────

def get_orcamentos_mes(conn, mes, ano):
    """Retorna orçamentos do mês com info da categoria."""
    sql = ("SELECT o.id, o.categoria_id, o.valor_limite, c.nome, c.icone "
           "FROM orcamentos o JOIN categorias c ON o.categoria_id = c.id "
           "WHERE o.mes=? AND o.ano=? ORDER BY c.nome")
    return read_sql(sql, conn, params=(mes, ano))


# ─── Metas ────────────────────────────────────────────────────────────────────

def get_metas(conn):
    """Retorna DataFrame de todas as metas."""
    return read_sql("SELECT * FROM metas ORDER BY id", conn)


# ─── Saldos Agregados ────────────────────────────────────────────────────────

def get_saldo_total(conn, saldo_conta_fn):
    """Calcula saldo total excluindo reserva e cartão de crédito."""
    from core.utils import TAXA_SIMPLES
    contas_normais = conn.execute(
        "SELECT id FROM contas WHERE tipo NOT IN ('Reserva de Emergência', 'Cartão de Crédito')"
    ).fetchall()
    saldo = sum(saldo_conta_fn(conn, r[0]) for r in contas_normais)
    rec_total = conn.execute("SELECT COALESCE(SUM(valor),0) FROM transacoes WHERE tipo='receita'").fetchone()[0]
    saldo -= rec_total * TAXA_SIMPLES
    return saldo


def get_saldo_reserva(conn, saldo_conta_fn):
    """Calcula saldo total das contas de reserva de emergência."""
    contas_reserva = conn.execute(
        "SELECT id FROM contas WHERE tipo = 'Reserva de Emergência'"
    ).fetchall()
    return sum(saldo_conta_fn(conn, r[0]) for r in contas_reserva)
