"""
Set a dedicated SQLite path before any `app` import so tests never touch services/data/booma.db.
This module must not import `app` at load time.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

_fd, _BOOMA_TEST_DB = tempfile.mkstemp(prefix="booma_pytest_", suffix=".db")
os.close(_fd)
os.environ["BOOMA_SQLITE_PATH"] = _BOOMA_TEST_DB
TEST_DB_PATH = Path(_BOOMA_TEST_DB)


def pytest_sessionfinish(session, exitstatus) -> None:
    TEST_DB_PATH.unlink(missing_ok=True)
