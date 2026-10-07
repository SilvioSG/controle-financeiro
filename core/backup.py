"""
core/backup.py — Snapshot JSON de todas as tabelas do schema public.

Uso:
    from core.backup import gerar_backup, backup_diario
    path = gerar_backup(raw_conn)        # snapshot imediato
    backup_diario(raw_conn)              # no máximo 1 por dia, mantém os últimos N
"""
import json
import os
from datetime import date, datetime
from decimal import Decimal

BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backups")
MANTER = 30


def _default(o):
    if isinstance(o, Decimal):
        return float(o)
    if isinstance(o, (datetime, date)):
        return o.isoformat()
    return str(o)


def _raw(conn):
    """Aceita DBConnection (wrapper) ou conexão psycopg2 crua."""
    return getattr(conn, "_conn", conn)


def snapshot(conn) -> dict:
    """Retorna {tabela: [linhas como dict]} de todas as tabelas do schema public."""
    cur = _raw(conn).cursor()
    cur.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema='public' AND table_type='BASE TABLE' ORDER BY table_name"
    )
    tabelas = [r[0] for r in cur.fetchall()]
    dados = {}
    for t in tabelas:
        cur.execute(f'SELECT * FROM public."{t}"')
        cols = [d[0] for d in cur.description]
        dados[t] = [dict(zip(cols, row)) for row in cur.fetchall()]
    return dados


def gerar_backup(conn, sufixo: str = "") -> str:
    """Grava backups/backup_YYYYMMDD_HHMMSS[_sufixo].json e retorna o caminho."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    nome = f"backup_{datetime.now():%Y%m%d_%H%M%S}{'_' + sufixo if sufixo else ''}.json"
    path = os.path.join(BACKUP_DIR, nome)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(snapshot(conn), f, ensure_ascii=False, indent=1, default=_default)
    return path


def backup_diario(conn):
    """Gera no máximo um backup automático por dia e apaga os mais antigos."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    hoje = f"{date.today():%Y%m%d}"
    auto = sorted(f for f in os.listdir(BACKUP_DIR) if f.endswith("_auto.json"))
    if any(f.startswith(f"backup_{hoje}") for f in auto):
        return None
    path = gerar_backup(conn, "auto")
    auto.append(os.path.basename(path))
    for antigo in sorted(auto)[:-MANTER]:
        try:
            os.remove(os.path.join(BACKUP_DIR, antigo))
        except OSError:
            pass
    return path


def exportar_json(conn) -> bytes:
    """Snapshot completo em bytes, para st.download_button."""
    return json.dumps(snapshot(conn), ensure_ascii=False, indent=1, default=_default).encode("utf-8")
