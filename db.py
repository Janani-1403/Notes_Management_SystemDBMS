"""
db.py – Database layer for Smart Notes Management System
Handles connection, table bootstrap, and all CRUD helpers.
"""

import mysql.connector
from mysql.connector import Error
import streamlit as st
from datetime import datetime

# ── Connection ────────────────────────────────────────────────────────────────

def _secret(key, default):
    """Safely read from st.secrets; fall back to default if secrets file missing."""
    try:
        return st.secrets[key]
    except Exception:
        return default


def get_connection():
    """Return a live MySQL connection.
    
    Credentials are read from .streamlit/secrets.toml if it exists,
    otherwise the defaults below are used directly — no secrets file required.
    
    Edit the defaults here OR create .streamlit/secrets.toml with your values.
    """
    cfg = {
        "host":       _secret("DB_HOST", "localhost"),
        "port":   int(_secret("DB_PORT", 3306)),
        "user":       _secret("DB_USER", "root"),
        "password":   _secret("DB_PASS", "Janani@14"),          # ← set your MySQL password here
        "database":   _secret("DB_NAME", "smart_notes_db"),
        "autocommit": True,
        "charset":    "utf8mb4",
    }
    return mysql.connector.connect(**cfg)


def run_query(sql: str, params=None, fetch=False):
    """Generic helper – runs sql, optionally returns rows as list[dict]."""
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params or ())
        if fetch:
            return cur.fetchall()
        conn.commit()
        return cur.lastrowid
    except Error as e:
        st.error(f"Database error: {e}")
        return [] if fetch else None
    finally:
        conn.close()


# ── Bootstrap ─────────────────────────────────────────────────────────────────

DDL = """
CREATE TABLE IF NOT EXISTS notes (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    title         VARCHAR(255)  NOT NULL,
    content       TEXT          NOT NULL,
    priority      ENUM('low','medium','high','urgent') DEFAULT 'medium',
    location      VARCHAR(500)  DEFAULT NULL,
    is_pinned     TINYINT(1)    DEFAULT 0,
    is_deleted    TINYINT(1)    DEFAULT 0,
    created_at    DATETIME      DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME      DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at    DATETIME      DEFAULT NULL
);

CREATE TABLE IF NOT EXISTS tags (
    id    INT AUTO_INCREMENT PRIMARY KEY,
    name  VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS note_tags (
    note_id INT NOT NULL,
    tag_id  INT NOT NULL,
    PRIMARY KEY (note_id, tag_id),
    FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id)  REFERENCES tags(id)  ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS versions (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    note_id      INT          NOT NULL,
    title        VARCHAR(255) NOT NULL,
    content      TEXT         NOT NULL,
    priority     ENUM('low','medium','high','urgent') DEFAULT 'medium',
    location     VARCHAR(500) DEFAULT NULL,
    saved_at     DATETIME     DEFAULT CURRENT_TIMESTAMP,
    version_num  INT          NOT NULL DEFAULT 1,
    FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS reminders (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    note_id      INT          DEFAULT NULL,
    description  VARCHAR(500) NOT NULL,
    remind_at    DATETIME     NOT NULL,
    is_done      TINYINT(1)   DEFAULT 0,
    is_deleted   TINYINT(1)   DEFAULT 0,
    created_at   DATETIME     DEFAULT CURRENT_TIMESTAMP,
    done_at      DATETIME     DEFAULT NULL,
    deleted_at   DATETIME     DEFAULT NULL,
    FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS events (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    title        VARCHAR(255) NOT NULL,
    description  TEXT         DEFAULT NULL,
    event_type   ENUM('general','scheduled') DEFAULT 'general',
    event_date   DATE         DEFAULT NULL,
    is_deleted   TINYINT(1)   DEFAULT 0,
    created_at   DATETIME     DEFAULT CURRENT_TIMESTAMP,
    deleted_at   DATETIME     DEFAULT NULL
);
"""

def bootstrap_db():
    """Create all tables if they don't exist."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        for stmt in DDL.strip().split(";"):
            stmt = stmt.strip()
            if stmt:
                cur.execute(stmt)
        conn.commit()
    except Error as e:
        st.error(f"Bootstrap error: {e}")
    finally:
        conn.close()


# ══════════════════════════════════════════════════════════════════════════════
# NOTES
# ══════════════════════════════════════════════════════════════════════════════

def create_note(title, content, priority, location, tags_list):
    note_id = run_query(
        "INSERT INTO notes (title, content, priority, location) VALUES (%s,%s,%s,%s)",
        (title, content, priority, location or None)
    )
    if note_id and tags_list:
        _sync_tags(note_id, tags_list)
    return note_id


def get_notes(search="", priority_filter=None, tag_filter=None,
              include_deleted=False, pinned_only=False):
    where = ["n.is_deleted = %s"]
    params = [1 if include_deleted else 0]

    if pinned_only:
        where.append("n.is_pinned = 1")
    if priority_filter and priority_filter != "All":
        where.append("n.priority = %s")
        params.append(priority_filter.lower())
    if search:
        where.append("(n.title LIKE %s OR n.content LIKE %s)")
        params += [f"%{search}%", f"%{search}%"]

    tag_join = ""
    if tag_filter and tag_filter != "All":
        tag_join = "JOIN note_tags nt ON n.id = nt.note_id JOIN tags t ON nt.tag_id = t.id"
        where.append("t.name = %s")
        params.append(tag_filter)

    sql = f"""
        SELECT DISTINCT n.*,
            GROUP_CONCAT(DISTINCT tg.name ORDER BY tg.name SEPARATOR ',') AS tags
        FROM notes n
        LEFT JOIN note_tags ntg ON n.id = ntg.note_id
        LEFT JOIN tags tg ON ntg.tag_id = tg.id
        {tag_join}
        WHERE {' AND '.join(where)}
        GROUP BY n.id
        ORDER BY n.is_pinned DESC, n.updated_at DESC
    """
    return run_query(sql, params, fetch=True)


def get_note_by_id(note_id):
    rows = run_query(
        """SELECT n.*,
               GROUP_CONCAT(DISTINCT t.name ORDER BY t.name SEPARATOR ',') AS tags
           FROM notes n
           LEFT JOIN note_tags nt ON n.id = nt.note_id
           LEFT JOIN tags t ON nt.tag_id = t.id
           WHERE n.id = %s
           GROUP BY n.id""",
        (note_id,), fetch=True
    )
    return rows[0] if rows else None


def update_note(note_id, title, content, priority, location, tags_list):
    # Save current state as version first
    old = get_note_by_id(note_id)
    if old:
        _save_version(old)
    run_query(
        "UPDATE notes SET title=%s, content=%s, priority=%s, location=%s, updated_at=NOW() WHERE id=%s",
        (title, content, priority, location or None, note_id)
    )
    _sync_tags(note_id, tags_list)


def soft_delete_note(note_id):
    run_query(
        "UPDATE notes SET is_deleted=1, deleted_at=NOW() WHERE id=%s", (note_id,)
    )


def restore_note(note_id):
    run_query(
        "UPDATE notes SET is_deleted=0, deleted_at=NULL WHERE id=%s", (note_id,)
    )


def permanent_delete_note(note_id):
    run_query("DELETE FROM notes WHERE id=%s", (note_id,))


def toggle_pin(note_id, current_pin):
    run_query(
        "UPDATE notes SET is_pinned=%s WHERE id=%s", (0 if current_pin else 1, note_id)
    )


# ══════════════════════════════════════════════════════════════════════════════
# TAGS
# ══════════════════════════════════════════════════════════════════════════════

def _get_or_create_tag(name):
    name = name.strip().lower()
    rows = run_query("SELECT id FROM tags WHERE name=%s", (name,), fetch=True)
    if rows:
        return rows[0]["id"]
    return run_query("INSERT INTO tags (name) VALUES (%s)", (name,))


def _sync_tags(note_id, tags_list):
    run_query("DELETE FROM note_tags WHERE note_id=%s", (note_id,))
    for t in tags_list:
        t = t.strip()
        if t:
            tid = _get_or_create_tag(t)
            run_query("INSERT IGNORE INTO note_tags (note_id, tag_id) VALUES (%s,%s)", (note_id, tid))


def get_all_tags():
    rows = run_query("SELECT name FROM tags ORDER BY name", fetch=True)
    return [r["name"] for r in rows]


# ══════════════════════════════════════════════════════════════════════════════
# VERSIONS
# ══════════════════════════════════════════════════════════════════════════════

def _save_version(note_row):
    rows = run_query(
        "SELECT COALESCE(MAX(version_num),0)+1 AS nxt FROM versions WHERE note_id=%s",
        (note_row["id"],), fetch=True
    )
    nxt = rows[0]["nxt"] if rows else 1
    run_query(
        "INSERT INTO versions (note_id, title, content, priority, location, version_num) VALUES (%s,%s,%s,%s,%s,%s)",
        (note_row["id"], note_row["title"], note_row["content"],
         note_row["priority"], note_row["location"], nxt)
    )


def get_versions(note_id):
    return run_query(
        "SELECT * FROM versions WHERE note_id=%s ORDER BY version_num DESC", (note_id,), fetch=True
    )


def restore_version(note_id, version_id):
    rows = run_query("SELECT * FROM versions WHERE id=%s", (version_id,), fetch=True)
    if not rows:
        return
    v = rows[0]
    old = get_note_by_id(note_id)
    if old:
        _save_version(old)
    run_query(
        "UPDATE notes SET title=%s, content=%s, priority=%s, location=%s, updated_at=NOW() WHERE id=%s",
        (v["title"], v["content"], v["priority"], v["location"], note_id)
    )


# ══════════════════════════════════════════════════════════════════════════════
# REMINDERS
# ══════════════════════════════════════════════════════════════════════════════

def create_reminder(description, remind_at, note_id=None):
    return run_query(
        "INSERT INTO reminders (description, remind_at, note_id) VALUES (%s,%s,%s)",
        (description, remind_at, note_id)
    )


def get_reminders(status="upcoming", include_deleted=False):
    now = datetime.now()
    where = ["is_deleted = %s"]
    params = [1 if include_deleted else 0]

    if not include_deleted:
        if status == "upcoming":
            where += ["is_done=0", "remind_at >= %s"]
            params.append(now)
        elif status == "expired":
            where += ["is_done=0", "remind_at < %s"]
            params.append(now)
        elif status == "done":
            where.append("is_done=1")

    sql = f"SELECT * FROM reminders WHERE {' AND '.join(where)} ORDER BY remind_at ASC"
    return run_query(sql, params, fetch=True)


def mark_reminder_done(reminder_id):
    run_query(
        "UPDATE reminders SET is_done=1, done_at=NOW() WHERE id=%s", (reminder_id,)
    )


def soft_delete_reminder(reminder_id):
    run_query(
        "UPDATE reminders SET is_deleted=1, deleted_at=NOW() WHERE id=%s", (reminder_id,)
    )


def restore_reminder(reminder_id):
    run_query(
        "UPDATE reminders SET is_deleted=0, deleted_at=NULL WHERE id=%s", (reminder_id,)
    )


def permanent_delete_reminder(reminder_id):
    run_query("DELETE FROM reminders WHERE id=%s", (reminder_id,))


# ══════════════════════════════════════════════════════════════════════════════
# EVENTS
# ══════════════════════════════════════════════════════════════════════════════

def create_event(title, description, event_type, event_date=None):
    return run_query(
        "INSERT INTO events (title, description, event_type, event_date) VALUES (%s,%s,%s,%s)",
        (title, description, event_type, event_date)
    )


def get_events(view="general", include_deleted=False):
    now = datetime.now().date()
    where = ["is_deleted = %s"]
    params = [1 if include_deleted else 0]

    if not include_deleted:
        if view == "general":
            where.append("event_type='general'")
        elif view == "upcoming":
            where += ["event_type='scheduled'", "event_date >= %s"]
            params.append(now)
        elif view == "past":
            where += ["event_type='scheduled'", "event_date < %s"]
            params.append(now)

    order = "event_date ASC" if view in ("upcoming",) else "created_at DESC"
    sql = f"SELECT * FROM events WHERE {' AND '.join(where)} ORDER BY {order}"
    return run_query(sql, params, fetch=True)


def soft_delete_event(event_id):
    run_query(
        "UPDATE events SET is_deleted=1, deleted_at=NOW() WHERE id=%s", (event_id,)
    )


def restore_event(event_id):
    run_query(
        "UPDATE events SET is_deleted=0, deleted_at=NULL WHERE id=%s", (event_id,)
    )


def permanent_delete_event(event_id):
    run_query("DELETE FROM events WHERE id=%s", (event_id,))


# ══════════════════════════════════════════════════════════════════════════════
# ANALYTICS
# ══════════════════════════════════════════════════════════════════════════════

def get_dashboard_stats():
    stats = {}
    r = run_query("SELECT COUNT(*) AS c FROM notes WHERE is_deleted=0", fetch=True)
    stats["total_notes"] = r[0]["c"] if r else 0

    r = run_query("SELECT COUNT(*) AS c FROM notes WHERE is_deleted=0 AND is_pinned=1", fetch=True)
    stats["pinned"] = r[0]["c"] if r else 0

    r = run_query(
        "SELECT COUNT(*) AS c FROM reminders WHERE is_deleted=0 AND is_done=0 AND remind_at >= NOW()",
        fetch=True
    )
    stats["active_reminders"] = r[0]["c"] if r else 0

    r = run_query(
        "SELECT COUNT(*) AS c FROM reminders WHERE is_deleted=0 AND is_done=0 AND remind_at < NOW()",
        fetch=True
    )
    stats["overdue_reminders"] = r[0]["c"] if r else 0

    r = run_query("SELECT COUNT(*) AS c FROM events WHERE is_deleted=0", fetch=True)
    stats["total_events"] = r[0]["c"] if r else 0

    r = run_query(
        "SELECT priority, COUNT(*) AS c FROM notes WHERE is_deleted=0 GROUP BY priority",
        fetch=True
    )
    stats["by_priority"] = {row["priority"]: row["c"] for row in r}

    r = run_query(
        "SELECT COUNT(*) AS c FROM notes WHERE is_deleted=0 AND DATE(created_at)=CURDATE()",
        fetch=True
    )
    stats["today_notes"] = r[0]["c"] if r else 0

    return stats
