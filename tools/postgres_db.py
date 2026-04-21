import json
import os
from datetime import datetime
import psycopg2
import psycopg2.extras
from psycopg2.extras import Json
from config import (
    POSTGRES_HOST,
    POSTGRES_PORT,
    POSTGRES_DB,
    POSTGRES_USER,
    POSTGRES_PASSWORD,
    CLOUD_SQL_CONNECTION_NAME,
)


def _conn() -> psycopg2.extensions.connection:
    # On Cloud Run, use Unix socket via Cloud SQL Auth Proxy
    if CLOUD_SQL_CONNECTION_NAME:
        host = f"/cloudsql/{CLOUD_SQL_CONNECTION_NAME}"
        return psycopg2.connect(
            dbname=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            host=host,
        )
    return psycopg2.connect(
        host=POSTGRES_HOST,
        port=int(POSTGRES_PORT),
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
    )


_SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "..", "db", "schema.sql")


def init_db() -> None:
    with open(_SCHEMA_PATH) as f:
        ddl = f.read()
    with _conn() as con:
        with con.cursor() as cur:
            cur.execute(ddl)


def save_run(state: dict) -> int:
    sql = """
        INSERT INTO runs (
            query, company, region, risk_score, risk_label,
            judge_verdict, bear_analysis, bull_analysis,
            geopolitical_analysis, guardrail_report, final_output,
            partial_context, failed_sources, created_at
        ) VALUES (
            %(query)s, %(company)s, %(region)s, %(risk_score)s, %(risk_label)s,
            %(judge_verdict)s, %(bear_analysis)s, %(bull_analysis)s,
            %(geopolitical_analysis)s, %(guardrail_report)s, %(final_output)s,
            %(partial_context)s, %(failed_sources)s, %(created_at)s
        ) RETURNING id;
    """
    params = {
        "query": state.get("query", ""),
        "company": state.get("company", ""),
        "region": state.get("region", ""),
        "risk_score": state.get("risk_score"),
        "risk_label": (state.get("final_output") or {}).get("risk_label", ""),
        "judge_verdict": state.get("judge_verdict", ""),
        "bear_analysis": state.get("bear_analysis", ""),
        "bull_analysis": state.get("bull_analysis", ""),
        "geopolitical_analysis": state.get("geopolitical_analysis", ""),
        "guardrail_report": Json(state.get("guardrail_report") or {}),
        "final_output": Json(state.get("final_output") or {}),
        "partial_context": bool(state.get("partial_context", False)),
        "failed_sources": state.get("failed_sources") or [],
        "created_at": datetime.utcnow().isoformat(),
    }
    with _conn() as con:
        with con.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchone()[0]


def get_recent_runs(limit: int = 20) -> list[dict]:
    with _conn() as con:
        with con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM runs ORDER BY created_at DESC LIMIT %s", (limit,))
            return [dict(r) for r in cur.fetchall()]


def get_run_by_id(run_id: int) -> dict | None:
    with _conn() as con:
        with con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM runs WHERE id = %s", (run_id,))
            row = cur.fetchone()
    return dict(row) if row else None
