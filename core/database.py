"""
core/database.py — Conexão, inicialização e seeds do banco de dados.
Suporta SQLite (dev local) e PostgreSQL/Supabase (produção).
"""
import streamlit as st
import sqlite3
import re
import threading


# ─── Wrapper de Conexão ──────────────────────────────────────────────────────

class DBConnection:
    """Wrapper que abstrai diferenças entre SQLite e PostgreSQL.

    Converte automaticamente:
    - Placeholders: ? → %s (para PostgreSQL)
    - Funciona de forma transparente com pd.read_sql_query()
    """

    def __init__(self, conn, is_postgres=False):
        self._conn = conn
        self.is_postgres = is_postgres
        self.lock = threading.Lock()

    def _set_rls(self, cur):
        user_id = st.session_state.get("user_id")
        if user_id and self.is_postgres:
            cur.execute("SELECT set_config('request.jwt.claim.sub', %s, false)", (str(user_id),))

    def execute(self, sql, params=None):
        with self.lock:
            cur = self._conn.cursor()
            self._set_rls(cur)
            if self.is_postgres:
                sql = re.sub(r'\?', '%s', sql)
            if params:
                cur.execute(sql, params)
            else:
                cur.execute(sql)
            return cur

    def executemany(self, sql, params_list):
        with self.lock:
            cur = self._conn.cursor()
            self._set_rls(cur)
            if self.is_postgres:
                sql = re.sub(r'\?', '%s', sql)
                params_list = [tuple(p) if isinstance(p, list) else p for p in params_list]
            cur.executemany(sql, params_list)
            return cur

    def commit(self):
        self._conn.commit()

    def cursor(self):
        return self._conn.cursor()

    # Para pd.read_sql_query funcionar, precisa expor a interface do connection
    def __getattr__(self, name):
        return getattr(self._conn, name)


def read_sql(sql, conn, params=None):
    """Wrapper para pd.read_sql_query que converte placeholders automaticamente."""
    import pandas as pd
    import warnings
    if getattr(conn, 'is_postgres', False):
        sql = re.sub(r'\?', '%s', sql)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', UserWarning)
        if params:
            return pd.read_sql_query(sql, conn, params=params)
        return pd.read_sql_query(sql, conn)


# ─── Conexão ──────────────────────────────────────────────────────────────────

@st.cache_resource
def get_connection():
    """Retorna conexão singleton — PostgreSQL (Supabase) ou SQLite (local)."""

    # Tenta conectar ao Supabase se as credenciais estiverem configuradas
    if "supabase" in st.secrets and "url" in st.secrets["supabase"]:
        try:
            import psycopg2
            conn = psycopg2.connect(st.secrets["supabase"]["url"])
            conn.autocommit = False
            return DBConnection(conn, is_postgres=True)
        except Exception as e:
            st.warning(f"⚠️ Falha ao conectar ao Supabase: {e}. Usando SQLite local.")

    # Fallback: SQLite local
    conn = sqlite3.connect("financas.db", check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return DBConnection(conn, is_postgres=False)


# ─── Inicialização do Banco ──────────────────────────────────────────────────

def init_db(conn):
    """Cria todas as tabelas necessárias (compatível SQLite e PostgreSQL)."""

    if conn.is_postgres:
        _init_db_postgres(conn)
    else:
        _init_db_sqlite(conn)


def _init_db_sqlite(conn):
    """Cria tabelas no SQLite."""
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS contas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        tipo TEXT NOT NULL,
        icone TEXT DEFAULT '🏦',
        saldo_inicial REAL DEFAULT 0
    )""")

    try:
        c.execute("ALTER TABLE contas ADD COLUMN limite_cartao REAL DEFAULT 0")
        c.execute("ALTER TABLE contas ADD COLUMN dia_fechamento INTEGER DEFAULT 1")
        c.execute("ALTER TABLE contas ADD COLUMN dia_vencimento INTEGER DEFAULT 10")
    except sqlite3.OperationalError:
        pass

    c.execute("""CREATE TABLE IF NOT EXISTS categorias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        icone TEXT DEFAULT '📌',
        tipo TEXT DEFAULT 'ambos'
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS transacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo TEXT NOT NULL,
        descricao TEXT NOT NULL,
        valor REAL NOT NULL,
        data TEXT NOT NULL,
        categoria_id INTEGER,
        conta_id INTEGER,
        FOREIGN KEY (categoria_id) REFERENCES categorias(id),
        FOREIGN KEY (conta_id) REFERENCES contas(id)
    )""")

    try:
        c.execute("ALTER TABLE transacoes ADD COLUMN recorrente INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE transacoes ADD COLUMN observacao TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass

    c.execute("""CREATE TABLE IF NOT EXISTS metas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        valor_meta REAL NOT NULL,
        valor_atual REAL DEFAULT 0
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS orcamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        categoria_id INTEGER,
        valor_limite REAL NOT NULL,
        mes INTEGER NOT NULL,
        ano INTEGER NOT NULL,
        FOREIGN KEY (categoria_id) REFERENCES categorias(id),
        UNIQUE(categoria_id, mes, ano)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL UNIQUE,
        cor TEXT DEFAULT '#4e8cff'
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS transacao_tags (
        transacao_id INTEGER,
        tag_id INTEGER,
        PRIMARY KEY (transacao_id, tag_id),
        FOREIGN KEY (transacao_id) REFERENCES transacoes(id) ON DELETE CASCADE,
        FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS recorrentes_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        prefixo_mes TEXT NOT NULL,
        transacao_origem_id INTEGER,
        processado_em TEXT NOT NULL,
        UNIQUE(prefixo_mes, transacao_origem_id)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS mapeamento_categorias (
        palavra TEXT PRIMARY KEY,
        categoria_id INTEGER,
        FOREIGN KEY (categoria_id) REFERENCES categorias(id)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS atalhos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        descricao TEXT NOT NULL,
        valor REAL NOT NULL,
        categoria_id INTEGER,
        conta_id INTEGER,
        icone TEXT DEFAULT '⚡',
        tipo TEXT DEFAULT 'despesa',
        FOREIGN KEY (categoria_id) REFERENCES categorias(id),
        FOREIGN KEY (conta_id) REFERENCES contas(id)
    )""")

    conn.commit()


def _init_db_postgres(conn):
    """Cria tabelas no PostgreSQL (Supabase)."""
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS contas (
        id SERIAL PRIMARY KEY,
        nome TEXT NOT NULL,
        tipo TEXT NOT NULL,
        icone TEXT DEFAULT '🏦',
        saldo_inicial DOUBLE PRECISION DEFAULT 0,
        limite_cartao DOUBLE PRECISION DEFAULT 0,
        dia_fechamento INTEGER DEFAULT 1,
        dia_vencimento INTEGER DEFAULT 10
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS categorias (
        id SERIAL PRIMARY KEY,
        nome TEXT NOT NULL,
        icone TEXT DEFAULT '📌',
        tipo TEXT DEFAULT 'ambos'
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS transacoes (
        id SERIAL PRIMARY KEY,
        tipo TEXT NOT NULL,
        descricao TEXT NOT NULL,
        valor DOUBLE PRECISION NOT NULL,
        data TEXT NOT NULL,
        categoria_id INTEGER REFERENCES categorias(id),
        conta_id INTEGER REFERENCES contas(id),
        recorrente INTEGER DEFAULT 0,
        observacao TEXT DEFAULT ''
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS metas (
        id SERIAL PRIMARY KEY,
        nome TEXT NOT NULL,
        valor_meta DOUBLE PRECISION NOT NULL,
        valor_atual DOUBLE PRECISION DEFAULT 0
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS orcamentos (
        id SERIAL PRIMARY KEY,
        categoria_id INTEGER REFERENCES categorias(id),
        valor_limite DOUBLE PRECISION NOT NULL,
        mes INTEGER NOT NULL,
        ano INTEGER NOT NULL,
        UNIQUE(categoria_id, mes, ano)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS tags (
        id SERIAL PRIMARY KEY,
        nome TEXT NOT NULL UNIQUE,
        cor TEXT DEFAULT '#4e8cff'
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS transacao_tags (
        transacao_id INTEGER REFERENCES transacoes(id) ON DELETE CASCADE,
        tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
        PRIMARY KEY (transacao_id, tag_id)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS recorrentes_log (
        id SERIAL PRIMARY KEY,
        prefixo_mes TEXT NOT NULL,
        transacao_origem_id INTEGER,
        processado_em TEXT NOT NULL,
        UNIQUE(prefixo_mes, transacao_origem_id)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS mapeamento_categorias (
        palavra TEXT PRIMARY KEY,
        categoria_id INTEGER REFERENCES categorias(id)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS atalhos (
        id SERIAL PRIMARY KEY,
        descricao TEXT NOT NULL,
        valor DOUBLE PRECISION NOT NULL,
        categoria_id INTEGER REFERENCES categorias(id),
        conta_id INTEGER REFERENCES contas(id),
        icone TEXT DEFAULT '⚡',
        tipo TEXT DEFAULT 'despesa'
    )""")

    conn.commit()


# ─── Seeds ────────────────────────────────────────────────────────────────────

def seed_categorias(conn):
    """Insere categorias padrão se a tabela estiver vazia."""
    if conn.execute("SELECT COUNT(*) FROM categorias").fetchone()[0] == 0:
        cats = [
            ("Alimentação", "🍔", "despesa"), ("Transporte", "🚗", "despesa"),
            ("Moradia", "🏠", "despesa"), ("Saúde", "💊", "despesa"),
            ("Educação", "📚", "despesa"), ("Lazer", "🎮", "despesa"),
            ("Roupas", "👕", "despesa"), ("Assinaturas", "📺", "despesa"),
            ("Compras", "🛒", "despesa"), ("Cartão", "💳", "despesa"),
            ("Outros (Despesa)", "📦", "despesa"),
            ("Salário", "💰", "receita"), ("Freelance", "💻", "receita"),
            ("Investimentos", "📈", "receita"), ("Presente", "🎁", "receita"),
            ("Outros (Receita)", "💵", "receita"),
        ]
        conn.executemany("INSERT INTO categorias (nome, icone, tipo) VALUES (?,?,?)", cats)
        conn.commit()


def seed_conta_padrao(conn):
    """Insere conta 'Carteira' padrão se não houver contas."""
    if conn.execute("SELECT COUNT(*) FROM contas").fetchone()[0] == 0:
        conn.execute(
            "INSERT INTO contas (nome, tipo, icone, saldo_inicial) VALUES (?,?,?,?)",
            ("Carteira", "Carteira", "👛", 0),
        )
        conn.commit()


def saldo_conta(conn, conta_id):
    """Calcula o saldo atual de uma conta (saldo_inicial + receitas - despesas)."""
    row = conn.execute("SELECT saldo_inicial FROM contas WHERE id=?", (conta_id,)).fetchone()
    if not row:
        return 0
    s = row[0]
    s += conn.execute(
        "SELECT COALESCE(SUM(valor),0) FROM transacoes WHERE conta_id=? AND tipo='receita'",
        (conta_id,),
    ).fetchone()[0]
    s -= conn.execute(
        "SELECT COALESCE(SUM(valor),0) FROM transacoes WHERE conta_id=? AND tipo='despesa'",
        (conta_id,),
    ).fetchone()[0]
    return s
