import os
import importlib.util
import pytest
from sqlalchemy import text

from src.database import engine, get_session, close_session, init_db

POSTGRES_URL = os.getenv('DATABASE_URL', '')

requires_postgres = pytest.mark.skipif(
    'postgresql' not in POSTGRES_URL,
    reason='PostgreSQL not configured; skipping migration integration test.'
)


def _run_migration_script(path):
    spec = importlib.util.spec_from_file_location('add_oauth_support', path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f'Unable to load migration script spec for {path}')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore
    module.run_migration()


@requires_postgres
def test_add_oauth_migration_applies_once(tmp_path):
    # Ensure base schema exists
    init_db()
    migration_path = os.path.abspath('scripts/migrations/add_oauth_support.py')
    _run_migration_script(migration_path)

    session = get_session()
    try:
        # Verify columns exist
        result = session.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name='users' AND column_name IN ('oauth_provider','oauth_id','profile_picture')
        """))
        cols = {r[0] for r in result.fetchall()}
        assert {'oauth_provider','oauth_id','profile_picture'}.issubset(cols)

        # Run migration again (idempotency)
        _run_migration_script(migration_path)

        # Re-verify still intact
        result2 = session.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name='users' AND column_name IN ('oauth_provider','oauth_id','profile_picture')
        """))
        cols2 = {r[0] for r in result2.fetchall()}
        assert cols == cols2
    finally:
        close_session()
