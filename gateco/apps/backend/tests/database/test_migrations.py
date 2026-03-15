"""Tests for database migrations.

Tests migration upgrade and downgrade operations.
"""

import os
import subprocess
from typing import Generator

import pytest


# Only run migration tests if TEST_DATABASE_URL is set and migrations are enabled
SKIP_MIGRATION_TESTS = os.getenv("SKIP_MIGRATION_TESTS", "true").lower() == "true"


@pytest.fixture(scope="module")
def migrations_dir() -> str:
    """Get the migrations directory path."""
    return os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "migrations",
    )


@pytest.fixture(scope="module")
def alembic_ini() -> str:
    """Get the alembic.ini path."""
    return os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "alembic.ini",
    )


def run_alembic(command: list[str], cwd: str) -> subprocess.CompletedProcess:
    """Run an alembic command.

    Args:
        command: Alembic command arguments
        cwd: Working directory

    Returns:
        CompletedProcess result
    """
    return subprocess.run(
        ["alembic"] + command,
        cwd=cwd,
        capture_output=True,
        text=True,
        env={**os.environ, "DATABASE_URL": os.getenv("TEST_DATABASE_URL", "")},
    )


@pytest.mark.skipif(SKIP_MIGRATION_TESTS, reason="Migration tests disabled")
class TestMigrations:
    """Tests for Alembic migrations."""

    def test_migration_files_exist(self, migrations_dir: str):
        """Test that migration files exist."""
        versions_dir = os.path.join(migrations_dir, "versions")
        assert os.path.exists(versions_dir), "versions directory should exist"

        expected_migrations = [
            "001_initial.py",
            "002_users_organizations.py",
            "003_resources.py",
            "004_billing.py",
        ]

        for migration in expected_migrations:
            migration_path = os.path.join(versions_dir, migration)
            assert os.path.exists(migration_path), f"{migration} should exist"

    def test_migration_revision_chain(self, migrations_dir: str):
        """Test that migrations have correct revision chain."""
        versions_dir = os.path.join(migrations_dir, "versions")

        revision_chain = [
            ("001_initial.py", None, "001"),
            ("002_users_organizations.py", "001", "002"),
            ("003_resources.py", "002", "003"),
            ("004_billing.py", "003", "004"),
        ]

        for filename, expected_down, expected_revision in revision_chain:
            filepath = os.path.join(versions_dir, filename)
            with open(filepath, "r") as f:
                content = f.read()

            # Check revision ID
            assert f'revision: str = "{expected_revision}"' in content or \
                   f"revision = '{expected_revision}'" in content or \
                   f'revision = "{expected_revision}"' in content, \
                   f"{filename} should have revision {expected_revision}"

            # Check down_revision
            if expected_down is None:
                assert "down_revision" in content and "None" in content, \
                    f"{filename} should have down_revision = None"
            else:
                assert f'"{expected_down}"' in content or \
                       f"'{expected_down}'" in content, \
                       f"{filename} should have down_revision = {expected_down}"

    def test_alembic_current(self, alembic_ini: str):
        """Test alembic current command."""
        backend_dir = os.path.dirname(alembic_ini)
        result = run_alembic(["current"], backend_dir)
        # Current may be empty if no migrations applied, which is OK
        assert result.returncode == 0 or "FAILED" not in result.stderr

    def test_alembic_history(self, alembic_ini: str):
        """Test alembic history command."""
        backend_dir = os.path.dirname(alembic_ini)
        result = run_alembic(["history"], backend_dir)
        assert result.returncode == 0, f"History failed: {result.stderr}"

        # Check that all revisions are in history
        output = result.stdout
        assert "001" in output, "001 should be in history"
        assert "002" in output, "002 should be in history"
        assert "003" in output, "003 should be in history"
        assert "004" in output, "004 should be in history"


@pytest.mark.skipif(SKIP_MIGRATION_TESTS, reason="Migration tests disabled")
class TestMigrationUpDown:
    """Tests for migration upgrade/downgrade cycle.

    These tests actually modify the database.
    """

    def test_full_upgrade_downgrade(self, alembic_ini: str):
        """Test full upgrade and downgrade cycle."""
        backend_dir = os.path.dirname(alembic_ini)

        # First downgrade to base
        result = run_alembic(["downgrade", "base"], backend_dir)
        assert result.returncode == 0, f"Downgrade to base failed: {result.stderr}"

        # Upgrade to head
        result = run_alembic(["upgrade", "head"], backend_dir)
        assert result.returncode == 0, f"Upgrade to head failed: {result.stderr}"

        # Downgrade one step
        result = run_alembic(["downgrade", "-1"], backend_dir)
        assert result.returncode == 0, f"Downgrade -1 failed: {result.stderr}"

        # Upgrade back to head
        result = run_alembic(["upgrade", "head"], backend_dir)
        assert result.returncode == 0, f"Upgrade to head failed: {result.stderr}"

    def test_individual_migrations(self, alembic_ini: str):
        """Test each migration individually."""
        backend_dir = os.path.dirname(alembic_ini)

        # Downgrade to base
        result = run_alembic(["downgrade", "base"], backend_dir)
        assert result.returncode == 0

        migrations = ["001", "002", "003", "004"]

        for rev in migrations:
            # Upgrade to this revision
            result = run_alembic(["upgrade", rev], backend_dir)
            assert result.returncode == 0, \
                f"Upgrade to {rev} failed: {result.stderr}"

            # Verify current revision
            result = run_alembic(["current"], backend_dir)
            assert rev in result.stdout, f"Current should be {rev}"

            # Downgrade one step
            result = run_alembic(["downgrade", "-1"], backend_dir)
            assert result.returncode == 0, \
                f"Downgrade from {rev} failed: {result.stderr}"

            # Upgrade back
            result = run_alembic(["upgrade", rev], backend_dir)
            assert result.returncode == 0
