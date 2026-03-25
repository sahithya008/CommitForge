import sqlite3

def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        contributor_id INTEGER,
        assigned_reviewer_id INTEGER,
        title TEXT,
        description TEXT,
        category TEXT,
        demo_link TEXT,
        github_link TEXT,
        zip_path TEXT,
        status TEXT,
        assigned_at TEXT,
        created_at TEXT,
        updated_at TEXT,
        deleted_at TEXT
    )
    """)

    # Add missing columns to existing projects table if they are missing
    for col in ["assigned_reviewer_id", "assigned_at", "created_at", "updated_at", "deleted_at"]:
        try:
            col_type = "INTEGER" if col == "assigned_reviewer_id" else "TEXT"
            c.execute(f"ALTER TABLE projects ADD COLUMN {col} {col_type}")
        except sqlite3.OperationalError:
            pass

    c.execute("""
    CREATE TABLE IF NOT EXISTS project_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        contributor_id INTEGER,
        title TEXT,
        description TEXT,
        category TEXT,
        demo_link TEXT,
        github_link TEXT,
        zip_path TEXT,
        status TEXT,
        action TEXT,
        recorded_at TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        reviewer_id INTEGER,
        feedback TEXT,
        decision TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS project_reviewers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        reviewer_id INTEGER,
        assigned_at TEXT,
        UNIQUE(project_id, reviewer_id)
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        message TEXT,
        type TEXT,
        related_project_id INTEGER,
        read_status INTEGER DEFAULT 0,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()
