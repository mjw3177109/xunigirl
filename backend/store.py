"""Local SQLite persistence for sessions. No tokens or API keys are stored here."""
from __future__ import annotations
import sqlite3
import time
import uuid
from pathlib import Path

class Store:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.conn() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY, title TEXT NOT NULL, created_at REAL NOT NULL, updated_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                role TEXT NOT NULL CHECK(role IN ('user','assistant')),
                content TEXT NOT NULL, created_at REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS messages_session ON messages(session_id, id);
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                created_at REAL NOT NULL
            );
            ''')
    def conn(self):
        db = sqlite3.connect(str(self.path), timeout=5.0)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        db.execute('PRAGMA busy_timeout=5000')
        return db
    def create(self):
        ident = str(uuid.uuid4())
        now = time.time()
        with self.conn() as db:
            db.execute('INSERT INTO sessions VALUES(?,?,?,?)', (ident, '新对话', now, now))
            db.commit()
        return ident
    def exists(self, session_id):
        with self.conn() as db:
            return db.execute('SELECT 1 FROM sessions WHERE id=?', (session_id,)).fetchone() is not None
    def list_sessions(self):
        with self.conn() as db:
            return [dict(x) for x in db.execute('SELECT * FROM sessions ORDER BY updated_at DESC LIMIT 200')]
    def list_messages(self, session_id, limit=50):
        with self.conn() as db:
            return [dict(x) for x in db.execute('''SELECT role, content, created_at FROM (
                SELECT id,role,content,created_at FROM messages WHERE session_id=? ORDER BY id DESC LIMIT ?
            ) ORDER BY id ASC''', (session_id,limit))]
    def append(self, session_id, role, content):
        if role not in ('user','assistant'): raise ValueError('bad role')
        if not self.exists(session_id): raise KeyError('missing session')
        now=time.time()
        with self.conn() as db:
            db.execute('INSERT INTO messages(session_id,role,content,created_at) VALUES(?,?,?,?)',(session_id,role,content,now))
            db.execute('UPDATE sessions SET updated_at=?, title=CASE WHEN title=? AND ?=? THEN ? ELSE title END WHERE id=?',
                      (now,'新对话',role,'user',content[:34] or '新对话',session_id))
            db.commit()
    def delete(self, session_id):
        with self.conn() as db:
            db.execute('DELETE FROM sessions WHERE id=?',(session_id,))
            db.commit()

    def memories(self, limit=80):
        with self.conn() as db:
            return [dict(row) for row in db.execute(
                'SELECT id, content, created_at FROM memories ORDER BY id DESC LIMIT ?', (limit,))]

    def add_memory(self, content):
        content=content.strip()
        if not 1 <= len(content) <= 500:
            raise ValueError('memory text must have 1-500 characters')
        with self.conn() as db:
            cur=db.execute('INSERT INTO memories(content,created_at) VALUES(?,?)',(content,time.time()))
            db.commit()
            return cur.lastrowid

    def delete_memory(self, memory_id):
        with self.conn() as db:
            cur=db.execute('DELETE FROM memories WHERE id=?',(memory_id,))
            db.commit()
            return cur.rowcount > 0
