"""Disk-backed historical session library; metadata is separate from telemetry."""
import json
import os
import sqlite3
from collections.abc import Mapping
from pathlib import Path

DEFAULT_ROOT = Path(os.environ.get("F1_LAB_DATA", str(Path(__file__).resolve().parents[2] / ".local-data")))


class Library:
    def __init__(self, root=DEFAULT_ROOT):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "library.sqlite3"
        with self.connect() as db:
            db.executescript('''
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS sessions(id TEXT PRIMARY KEY, metadata TEXT NOT NULL, race TEXT);
                CREATE TABLE IF NOT EXISTS laps(id TEXT PRIMARY KEY, session_id TEXT NOT NULL,
                    summary TEXT NOT NULL, payload TEXT NOT NULL);
                CREATE INDEX IF NOT EXISTS laps_session ON laps(session_id);
                CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY, state TEXT NOT NULL,
                    message TEXT NOT NULL, request TEXT NOT NULL, session_id TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP);
            ''')

    def connect(self):
        db = sqlite3.connect(str(self.path), timeout=30)
        db.row_factory = sqlite3.Row
        return db

    def sessions(self):
        with self.connect() as db:
            return [json.loads(r[0]) for r in db.execute("SELECT metadata FROM sessions ORDER BY id DESC")]

    def session(self, key):
        with self.connect() as db:
            row = db.execute("SELECT metadata FROM sessions WHERE id=?", (key,)).fetchone()
        if row is None:
            raise KeyError(key)
        return json.loads(row[0])

    def race(self, key):
        with self.connect() as db:
            row = db.execute("SELECT race FROM sessions WHERE id=?", (key,)).fetchone()
        if row is None or row[0] is None:
            raise KeyError(key)
        return json.loads(row[0])

    def lap(self, key):
        with self.connect() as db:
            row = db.execute("SELECT payload FROM laps WHERE id=?", (key,)).fetchone()
        if row is None:
            raise KeyError(key)
        from telemetry_pit_crew.contracts import Lap
        return Lap.model_validate_json(row[0])

    def lap_summaries(self, session_id=None):
        with self.connect() as db:
            query = "SELECT summary FROM laps" + (" WHERE session_id=?" if session_id else "") + " ORDER BY id"
            return [json.loads(r[0]) for r in db.execute(query, (session_id,) if session_id else ())]

    def store(self, metadata, laps, race=None):
        """Replace one complete session atomically; never expose a half import."""
        metadata = dict(metadata, lap_ids=[lap.id for lap in laps], cached=True)
        if not laps and race is None:
            raise ValueError("Session has no usable timing or telemetry.")
        with self.connect() as db:
            db.execute("DELETE FROM laps WHERE session_id=?", (metadata['id'],))
            for lap in laps:
                db.execute("INSERT INTO laps VALUES(?,?,?,?)", (lap.id, metadata['id'],
                           json.dumps(lap.model_dump(exclude={'samples'}), allow_nan=False),
                           lap.model_dump_json()))
            db.execute("INSERT OR REPLACE INTO sessions VALUES(?,?,?)", (metadata['id'],
                       json.dumps(metadata, allow_nan=False), json.dumps(race, allow_nan=False) if race else None))

    def job(self, key):
        with self.connect() as db:
            row = db.execute("SELECT * FROM jobs WHERE id=?", (key,)).fetchone()
        if row is None:
            raise KeyError(key)
        item = dict(row)
        item['request'] = json.loads(item['request'])
        return item

    def update_job(self, key, state, message, session_id=None):
        with self.connect() as db:
            db.execute("UPDATE jobs SET state=?,message=?,session_id=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                       (state, message, session_id, key))


class SessionMap(Mapping):
    def __init__(self, library): self.library = library
    def __getitem__(self, key): return self.library.session(key)
    def __iter__(self): return iter(s['id'] for s in self.library.sessions())
    def __len__(self): return len(self.library.sessions())


class LapMap(Mapping):
    def __init__(self, library): self.library = library
    def __getitem__(self, key): return self.library.lap(key)
    def __iter__(self): return iter(s['id'] for s in self.library.lap_summaries())
    def __len__(self): return len(self.library.lap_summaries())
