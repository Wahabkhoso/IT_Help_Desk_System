"""
database.py
Central database connection and schema management for the IT Help Desk system.
Uses SQLite with parameterized queries throughout the application.
"""

import sqlite3
import os
from datetime import datetime
from utils.paths import get_app_dir

DB_DIR = os.path.join(get_app_dir(), "database")
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "helpdesk.db")


class Database:
    """
    Handles the SQLite connection lifecycle and schema creation.
    A single instance is shared across the application (simple singleton pattern).
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path=DB_PATH):
        if self._initialized:
            return
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.row_factory = sqlite3.Row
        self._initialized = True
        self.create_schema()

    # ------------------------------------------------------------------
    # Core query helpers
    # ------------------------------------------------------------------
    def execute(self, query, params=()):
        """Execute an INSERT/UPDATE/DELETE query and commit."""
        cur = self.conn.cursor()
        cur.execute(query, params)
        self.conn.commit()
        return cur

    def fetchone(self, query, params=()):
        cur = self.conn.cursor()
        cur.execute(query, params)
        return cur.fetchone()

    def fetchall(self, query, params=()):
        cur = self.conn.cursor()
        cur.execute(query, params)
        return cur.fetchall()

    def close(self):
        self.conn.close()

    # ------------------------------------------------------------------
    # Schema creation
    # ------------------------------------------------------------------
    def create_schema(self):
        cur = self.conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'employee', 'staff')),
            department TEXT,
            phone TEXT,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS support_staff (
            staff_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            specialty TEXT,
            max_active_tickets INTEGER DEFAULT 10,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            category_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            assigned_staff_id INTEGER,
            category_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            priority TEXT NOT NULL CHECK(priority IN ('Low','Medium','High','Critical')),
            status TEXT NOT NULL CHECK(status IN ('New','Assigned','In Progress','Resolved','Closed','Reopened')),
            attachment_path TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            resolved_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY (assigned_staff_id) REFERENCES support_staff(staff_id) ON DELETE SET NULL,
            FOREIGN KEY (category_id) REFERENCES categories(category_id)
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS ticket_comments (
            comment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER NOT NULL,
            author_user_id INTEGER NOT NULL,
            comment TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id) ON DELETE CASCADE,
            FOREIGN KEY (author_user_id) REFERENCES users(user_id)
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS ticket_history (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER NOT NULL,
            changed_by_user_id INTEGER,
            field_changed TEXT NOT NULL,
            old_value TEXT,
            new_value TEXT,
            changed_at TEXT NOT NULL,
            FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id) ON DELETE CASCADE,
            FOREIGN KEY (changed_by_user_id) REFERENCES users(user_id)
        )
        """)

        self.conn.commit()
        self._seed_categories()

    def _seed_categories(self):
        default_categories = [
            ("Hardware", "Physical equipment issues"),
            ("Software", "Application or OS issues"),
            ("Network", "LAN/WAN connectivity issues"),
            ("Internet", "Internet access issues"),
            ("Account/Login", "Authentication and access issues"),
            ("Email", "Email service issues"),
            ("Printer", "Printing and scanning issues"),
            ("Other", "Uncategorized issues"),
        ]
        for name, desc in default_categories:
            self.conn.execute(
                "INSERT OR IGNORE INTO categories (name, description) VALUES (?, ?)",
                (name, desc),
            )
        self.conn.commit()


def get_db():
    """Convenience accessor used across the app."""
    return Database()


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
