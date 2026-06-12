import sqlite3
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query

CLAWDIA_ROOT = Path(__file__).resolve().parent.parent.parent.parent
BRIDGE_DB = str(CLAWDIA_ROOT.parent / "Services" / "ClawdiaBridge" / "data" / "clawdia.db")

router = APIRouter(prefix="/api/db")


def get_db():
    if not Path(BRIDGE_DB).exists():
        raise HTTPException(404, f"Bridge database not found at {BRIDGE_DB}")
    conn = sqlite3.connect(BRIDGE_DB)
    conn.row_factory = sqlite3.Row
    return conn


@router.get("/tables")
def list_tables():
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        tables = []
        for r in rows:
            name = r["name"]
            count = conn.execute(
                f"SELECT COUNT(*) as c FROM [{name}]"
            ).fetchone()["c"]
            tables.append({"name": name, "rows": count})
        return {"tables": tables}
    finally:
        conn.close()


@router.get("/query")
def query_table(
    table: str = Query(...),
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0),
):
    conn = get_db()
    try:
        valid = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        valid_names = [r["name"] for r in valid]
        if table not in valid_names:
            raise HTTPException(400, f"Invalid table: {table}")

        total = conn.execute(f"SELECT COUNT(*) as c FROM [{table}]").fetchone()["c"]
        cur = conn.execute(
            f"SELECT * FROM [{table}] ORDER BY id DESC LIMIT ? OFFSET ?",
            (limit, offset),
        )
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description] if rows else []
        data = [dict(r) for r in rows]
        return {"table": table, "columns": columns, "rows": data, "total": total, "limit": limit, "offset": offset}
    finally:
        conn.close()
