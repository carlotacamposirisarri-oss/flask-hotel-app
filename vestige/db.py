"""SQLite persistence for Vestige Intelligence.

Single-file database under instance/. Every engagement-scoped table carries
brand_id so each maison's data stays isolated; the internal intelligence and
growth layers only ever read aggregates (see analytics.py).
"""
import json
import os
import sqlite3
from datetime import datetime

from flask import current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS brands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    sector TEXT DEFAULT '',
    market TEXT DEFAULT '',
    heritage TEXT DEFAULT '',
    core_values TEXT DEFAULT '',
    visual_codes TEXT DEFAULT '',
    tone_of_voice TEXT DEFAULT '',
    archetypes TEXT DEFAULT '',
    positioning TEXT DEFAULT '',
    strategic_gaps TEXT DEFAULT '',
    accent_color TEXT DEFAULT '#8C6A4A',
    map_x_label TEXT DEFAULT 'Heritage  ←→  Innovation',
    map_y_label TEXT DEFAULT 'Accessible  ←→  Exclusive',
    map_x INTEGER DEFAULT 35,
    map_y INTEGER DEFAULT 75,
    created_at TEXT, updated_at TEXT
);
CREATE TABLE IF NOT EXISTS competitors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand_id INTEGER NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    positioning TEXT DEFAULT '',
    client_tiers TEXT DEFAULT '',
    signals TEXT DEFAULT '',
    axis_x INTEGER DEFAULT 50,
    axis_y INTEGER DEFAULT 50,
    notes TEXT DEFAULT '',
    created_at TEXT
);
CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand_id INTEGER NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    email TEXT DEFAULT '',
    country TEXT DEFAULT '',
    city TEXT DEFAULT '',
    tier TEXT DEFAULT '',
    archetype TEXT DEFAULT '',
    phase TEXT DEFAULT 'Discovery',
    engagement_score INTEGER DEFAULT 50,
    lifetime_value REAL DEFAULT 0,
    interests TEXT DEFAULT '[]',
    affinities TEXT DEFAULT '{}',
    social_circle TEXT DEFAULT '[]',
    social_footprint TEXT DEFAULT '',
    cross_purchases TEXT DEFAULT '',
    behavioral_signals TEXT DEFAULT '',
    info_gaps TEXT DEFAULT '',
    notes TEXT DEFAULT '',
    source TEXT DEFAULT 'manual',
    created_at TEXT, updated_at TEXT
);
CREATE TABLE IF NOT EXISTS client_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    date TEXT, kind TEXT, description TEXT
);
CREATE TABLE IF NOT EXISTS crm_imports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand_id INTEGER NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
    filename TEXT, source_system TEXT,
    rows_total INTEGER, rows_imported INTEGER,
    mapping TEXT, created_at TEXT
);
-- Every AI-generated (or manually added) piece of strategic work: insights,
-- story arcs, community blueprints, initiatives, collaborations, CX maps,
-- audits, competitive analyses, intelligence briefs, growth plans...
-- `kind` selects the definition in prompts.KINDS; `payload` holds its fields.
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand_id INTEGER REFERENCES brands(id) ON DELETE CASCADE,
    scope TEXT NOT NULL DEFAULT 'brand',
    kind TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT DEFAULT '',
    payload TEXT DEFAULT '{}',
    status TEXT DEFAULT 'proposed',
    urgency INTEGER DEFAULT 3,
    impact INTEGER DEFAULT 3,
    priority INTEGER DEFAULT 0,
    month INTEGER,
    model TEXT DEFAULT '',
    brand_label TEXT DEFAULT '',
    prompt TEXT DEFAULT '',
    annotation TEXT DEFAULT '',
    created_at TEXT, updated_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_items_brand_kind ON items(brand_id, kind);
CREATE TABLE IF NOT EXISTS decks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand_id INTEGER REFERENCES brands(id) ON DELETE SET NULL,
    title TEXT, subtitle TEXT, audience TEXT DEFAULT 'client',
    slides TEXT DEFAULT '[]',
    model TEXT DEFAULT '',
    created_at TEXT, updated_at TEXT
);
CREATE TABLE IF NOT EXISTS kpis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    period TEXT, name TEXT, value REAL, unit TEXT DEFAULT '', note TEXT DEFAULT '',
    created_at TEXT
);
CREATE TABLE IF NOT EXISTS goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT, metric TEXT DEFAULT '', target REAL DEFAULT 0, current REAL DEFAULT 0,
    due TEXT DEFAULT '', status TEXT DEFAULT 'active', notes TEXT DEFAULT '',
    created_at TEXT, updated_at TEXT
);
CREATE TABLE IF NOT EXISTS saved_queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT, dimension TEXT, metric TEXT, sector TEXT DEFAULT '',
    created_at TEXT
);
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);
-- One full run of the engagement diagnostic pipeline for a maison:
-- segmentation -> archetypes -> cross-examination -> strategy -> report/deck.
CREATE TABLE IF NOT EXISTS diagnostics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand_id INTEGER NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
    status TEXT DEFAULT 'queued',
    stage TEXT DEFAULT '',
    error TEXT DEFAULT '',
    brief TEXT DEFAULT '',
    segmentation TEXT DEFAULT '{}',
    archetypes TEXT DEFAULT '{}',
    crossexam TEXT DEFAULT '{}',
    strategy TEXT DEFAULT '{}',
    model TEXT DEFAULT '',
    deck_id INTEGER,
    created_at TEXT, finished_at TEXT
);
-- Proactive mode: companies Vestige researches before they are clients.
CREATE TABLE IF NOT EXISTS prospects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company TEXT NOT NULL,
    sector TEXT DEFAULT '',
    market TEXT DEFAULT '',
    website TEXT DEFAULT '',
    stage TEXT DEFAULT 'Identified',
    fit_score INTEGER,
    why TEXT DEFAULT '',
    material TEXT DEFAULT '',
    notes TEXT DEFAULT '',
    run_status TEXT DEFAULT 'idle',
    run_stage TEXT DEFAULT '',
    error TEXT DEFAULT '',
    dossier TEXT DEFAULT '{}',
    pitch TEXT DEFAULT '{}',
    sources TEXT DEFAULT '[]',
    used_web INTEGER DEFAULT 0,
    model TEXT DEFAULT '',
    deck_id INTEGER,
    brand_id INTEGER REFERENCES brands(id) ON DELETE SET NULL,
    created_at TEXT, updated_at TEXT
);
"""

# Columns added after the first release; applied to existing databases on start.
MIGRATIONS = {
    "brands": {"current_strategy": "TEXT DEFAULT ''", "resource_allocation": "TEXT DEFAULT ''"},
    "competitors": {"actions": "TEXT DEFAULT ''"},
    "clients": {"purchase_categories": "TEXT DEFAULT '[]'", "purchase_count": "INTEGER DEFAULT 0",
                "first_purchase": "TEXT DEFAULT ''", "last_purchase": "TEXT DEFAULT ''",
                "avg_ticket": "REAL DEFAULT 0", "segment": "INTEGER"},
}

JSON_FIELDS = {"interests", "affinities", "social_circle", "payload", "slides", "mapping", "purchase_categories",
               "segmentation", "archetypes", "crossexam", "strategy", "dossier", "pitch", "sources"}
DICT_FIELDS = {"affinities", "payload", "mapping", "segmentation", "archetypes", "crossexam", "strategy", "dossier",
               "pitch"}


def now():
    return datetime.now().isoformat(timespec="seconds")


def db_path():
    return os.path.join(current_app.instance_path, "vestige.db")


def get_db():
    if "db" not in g:
        os.makedirs(current_app.instance_path, exist_ok=True)
        conn = sqlite3.connect(db_path())
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        g.db = conn
    return g.db


def close_db(_exc=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_db():
    conn = get_db()
    conn.executescript(SCHEMA)
    for table, cols in MIGRATIONS.items():
        existing = {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
        for col, ddl in cols.items():
            if col not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {ddl}")
    conn.commit()


def _decode(row):
    if row is None:
        return None
    d = dict(row)
    for k in JSON_FIELDS & d.keys():
        try:
            d[k] = json.loads(d[k] or ("{}" if k in DICT_FIELDS else "[]"))
        except (TypeError, ValueError):
            d[k] = {} if k in DICT_FIELDS else []
    return d


def query(sql, args=(), one=False):
    rows = get_db().execute(sql, args).fetchall()
    rows = [_decode(r) for r in rows]
    return (rows[0] if rows else None) if one else rows


def scalar(sql, args=()):
    row = get_db().execute(sql, args).fetchone()
    return row[0] if row else None


def _encode(values):
    out = {}
    for k, v in values.items():
        out[k] = json.dumps(v, ensure_ascii=False) if k in JSON_FIELDS and not isinstance(v, str) else v
    return out


def insert(table, values):
    values = _encode(values)
    cols = list(values)
    cur = get_db().execute(
        f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})",
        [values[c] for c in cols],
    )
    get_db().commit()
    return cur.lastrowid


def update(table, row_id, values):
    if not values:
        return
    values = _encode(values)
    cols = list(values)
    get_db().execute(
        f"UPDATE {table} SET {', '.join(f'{c} = ?' for c in cols)} WHERE id = ?",
        [values[c] for c in cols] + [row_id],
    )
    get_db().commit()


def delete(table, row_id):
    get_db().execute(f"DELETE FROM {table} WHERE id = ?", (row_id,))
    get_db().commit()


def get_setting(key, default=None):
    row = get_db().execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row[0] if row else default


def set_setting(key, value):
    get_db().execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )
    get_db().commit()
