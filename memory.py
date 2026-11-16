
import sqlite3
import os
from datetime import datetime

DB_NAME = os.path.join(
    os.getenv("JARVIS_DATA_DIR", "."),
    "jarvis_memory.db"
)

def connect():
    return sqlite3.connect(DB_NAME)


def now():
    return datetime.now().isoformat()


def initialize_memory():
    with connect() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS facts (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # Safely upgrade existing facts table.
        columns = [
            row[1] for row in db.execute(
                "PRAGMA table_info(facts)"
            ).fetchall()
        ]

        if "category" not in columns:
            db.execute("""
                ALTER TABLE facts
                ADD COLUMN category TEXT NOT NULL DEFAULT 'general'
            """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                details TEXT DEFAULT '',
                status TEXT DEFAULT 'active',
                updated_at TEXT NOT NULL
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                details TEXT DEFAULT '',
                status TEXT DEFAULT 'pending',
                project TEXT DEFAULT '',
                updated_at TEXT NOT NULL
            )
        """)


# CONVERSATION HISTORY

def save_message(role, content):
    if not content:
        return

    with connect() as db:
        db.execute("""
            INSERT INTO messages (role, content, created_at)
            VALUES (?, ?, ?)
        """, (role, content, now()))


def get_recent_messages(limit=20):
    with connect() as db:
        return db.execute("""
            SELECT role, content FROM messages
            ORDER BY id DESC LIMIT ?
        """, (limit,)).fetchall()


# PERSONAL FACTS

def remember_fact(key, value, category="general"):
    with connect() as db:
        db.execute("""
            INSERT INTO facts (key, value, updated_at, category)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at,
                category = excluded.category
        """, (key, value, now(), category))


def get_facts():
    with connect() as db:
        return db.execute("""
            SELECT key, value FROM facts
        """).fetchall()


def get_fact(key):
    with connect() as db:
        result = db.execute("""
            SELECT value FROM facts WHERE key = ?
        """, (key,)).fetchone()

    return result[0] if result else None


def search_facts(query):
    with connect() as db:
        return db.execute("""
            SELECT key, value, category FROM facts
            WHERE key LIKE ? OR value LIKE ?
        """, (f"%{query}%", f"%{query}%")).fetchall()


def forget_fact(key):
    with connect() as db:
        cursor = db.execute(
            "DELETE FROM facts WHERE key = ?", (key,)
        )
        return cursor.rowcount > 0


# PROJECT MANAGEMENT

def add_project(title, details=""):
    with connect() as db:
        db.execute("""
            INSERT INTO projects (title, details, status, updated_at)
            VALUES (?, ?, 'active', ?)
        """, (title, details, now()))


def get_projects():
    with connect() as db:
        return db.execute("""
            SELECT id, title, details, status
            FROM projects ORDER BY id DESC
        """).fetchall()


def update_project(project_id, status=None, details=None):
    with connect() as db:
        if status is not None:
            db.execute("""
                UPDATE projects SET status = ?, updated_at = ?
                WHERE id = ?
            """, (status, now(), project_id))

        if details is not None:
            db.execute("""
                UPDATE projects SET details = ?, updated_at = ?
                WHERE id = ?
            """, (details, now(), project_id))


# TASK MANAGEMENT

def add_task(title, details="", project=""):
    with connect() as db:
        db.execute("""
            INSERT INTO tasks
            (title, details, status, project, updated_at)
            VALUES (?, ?, 'pending', ?, ?)
        """, (title, details, project, now()))


def get_tasks(status=None):
    with connect() as db:
        if status:
            return db.execute("""
                SELECT id, title, details, status, project
                FROM tasks WHERE status = ?
                ORDER BY id DESC
            """, (status,)).fetchall()

        return db.execute("""
            SELECT id, title, details, status, project
            FROM tasks ORDER BY id DESC
        """).fetchall()


def update_task(task_id, status):
    with connect() as db:
        db.execute("""
            UPDATE tasks SET status = ?, updated_at = ?
            WHERE id = ?
        """, (status, now(), task_id))


def delete_task(task_id):
    with connect() as db:
        db.execute(
            "DELETE FROM tasks WHERE id = ?", (task_id,)
        )


# MEMORY CONTEXT FOR JARVIS

def get_memory_context():
    facts = get_facts()
    projects = get_projects()
    tasks = get_tasks(status="pending")

    lines = []

    if facts:
        lines.append("PERSONAL FACTS:")
        for key, value in facts:
            lines.append(f"- {key}: {value}")

    if projects:
        lines.append("\nPROJECTS:")
        for project_id, title, details, status in projects:
            lines.append(
                f"- {title} | Status: {status} | {details}"
            )

    if tasks:
        lines.append("\nPENDING TASKS:")
        for task_id, title, details, status, project in tasks:
            lines.append(
                f"- {title} | Project: {project} | {details}"
            )

    return "\n".join(lines) if lines else "No saved memories."


if __name__ == "__main__":
    initialize_memory()
    print("JARVIS MEMORY READY")
    print("FACTS:", get_facts())
    print("PROJECTS:", get_projects())
    print("TASKS:", get_tasks())
