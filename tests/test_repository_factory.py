from __future__ import annotations

from pathlib import Path

from infrastructure.logging_monitoring import LoggingMonitoring
from infrastructure.repository_factory import build_result_repository
from infrastructure.result_repository import MockResultRepository


def test_repository_factory_uses_mock_by_default(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("RESULT_BACKEND", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)

    repository = build_result_repository(
        tmp_path, LoggingMonitoring(logger_name="repo_factory_default")
    )

    assert isinstance(repository, MockResultRepository)


def test_repository_factory_falls_back_to_mock_when_postgres_is_missing(
    tmp_path: Path, monkeypatch
):
    monkeypatch.setenv("RESULT_BACKEND", "postgresql")
    monkeypatch.delenv("DATABASE_URL", raising=False)

    repository = build_result_repository(
        tmp_path, LoggingMonitoring(logger_name="repo_factory_fallback")
    )

    assert isinstance(repository, MockResultRepository)
