import sys
import os
import pytest

# Debug: print sys.path when conftest is imported
print(f"\n[CONFTEST] sys.path[0:3] at import time: {sys.path[0:3]}")
print(f"[CONFTEST] Current working directory: {os.getcwd()}")

# Patch pymongo IMMEDIATELY at conftest import time
# This happens before pytest tries to import test modules
import mongomock
import pymongo
pymongo.MongoClient = mongomock.MongoClient

# Add workspace root to sys.path so absolute imports work
conftest_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(conftest_dir))
print(f"[CONFTEST] root_dir: {root_dir}")
print(f"[CONFTEST] conftest_dir: {conftest_dir}")
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
    print(f"[CONFTEST] Inserted root_dir into sys.path")

print(f"[CONFTEST] sys.path[0:3] after insert: {sys.path[0:3]}")


def pytest_sessionstart(session):
    """
    This hook runs before test collection and execution.
    Inject the mongomock database into mongodb_connect.
    """
    print(f"\n[PYTEST_SESSIONSTART] sys.path[0:3]: {sys.path[0:3]}")
    try:
        from HealthFraudMLChain.database import mongodb_connect
        print(f"[PYTEST_SESSIONSTART] Successfully imported mongodb_connect")
        
        # Create a mongomock client and database
        mock_client = mongomock.MongoClient()
        mock_db = mock_client['healthfraud']
        
        # Inject into module (services will use these when they call get_db())
        mongodb_connect.client = mock_client
        mongodb_connect.db = mock_db
        mongodb_connect.TEST_MODE = True
        
        # Reset any earlier connections
        if hasattr(mongodb_connect, 'reset_db_for_testing'):
            mongodb_connect.reset_db_for_testing()
            
    except Exception as e:
        print(f"[PYTEST_SESSIONSTART] ERROR: {e}")
        pytest.skip(f"Could not setup mongodb_connect: {e}")


