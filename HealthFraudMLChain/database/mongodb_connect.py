# database/mongodb_connect.py

"""Lazy MongoDB connector with test injection support.

This module no longer opens a network connection on import. Call
`init_db(mongo_uri=None)` or `get_db()` at application runtime. Tests
can patch `pymongo.MongoClient` (e.g. with mongomock) BEFORE importing
modules that call `get_db()`. Tests can also set TEST_MODE=True and
inject a mongomock db via the public `db` variable.
"""
from typing import Optional
import os
from pymongo import MongoClient

# Prefer environment-configured URI; keep a default placeholder but do
# not connect at import time.
MONGO_URI = os.environ.get('MONGO_URI') or "mongodb+srv://<REDACTED>/healthfraud?retryWrites=true&w=majority"

# Global test mode flag: if True, services MUST use the global db below.
# conftest.py sets this to ensure mongomock stays active during tests.
TEST_MODE = False

# Public client/db references for test injection and lazy initialization.
# Tests can set these directly (e.g., db = mongomock_db).
client: Optional[MongoClient] = None
db = None

# Internal tracking flag
_initialized = False


def init_db(mongo_uri: Optional[str] = None):
    """Initialize the global DB client and database.

    Call this once at application startup (e.g. from `main.py`).
    Tests should patch `pymongo.MongoClient` BEFORE this is called.
    """
    global client, db, _initialized
    uri = mongo_uri or os.environ.get('MONGO_URI') or MONGO_URI
    if client is None:
        client = MongoClient(uri)
        db = client.get_database('healthfraud')
        _initialized = True
    return db


def get_db():
    """Return the initialized DB. If not initialized, initialize using
    the environment `MONGO_URI`.
    
    In TEST_MODE, always returns the global db (which conftest sets to mongomock).
    """
    global db, TEST_MODE
    # If in test mode and db is already set (by conftest), return it immediately
    if TEST_MODE and db is not None:
        return db
    # Otherwise, lazy-initialize on first call
    if db is None:
        return init_db()
    return db


def get_collection(name: str):
    """Convenience helper to access a collection lazily."""
    db = get_db()
    return db.get_collection(name)


def reset_db_for_testing():
    """Reset internal client/db references (test helper)."""
    global client, db, _initialized, TEST_MODE
    client = None
    db = None
    _initialized = False
    TEST_MODE = False
