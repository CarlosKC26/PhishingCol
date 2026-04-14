from __future__ import annotations

import os
from pathlib import Path

from infrastructure.logging_monitoring import LoggingMonitoring
from infrastructure.result_repository import MockResultRepository
from infrastructure.result_repository_postgresql import PostgreSQLResultRepository


def build_result_repository(
    root_path: Path,
    logger: LoggingMonitoring,
):
    backend = os.getenv("RESULT_BACKEND", "mock").strip().lower()
    if backend == "postgresql":
        database_url = os.getenv("DATABASE_URL", "").strip()
        if not database_url:
            logger.warning(
                "DATABASE_URL no configurado; se usará persistencia mock.",
                backend=backend,
            )
            return MockResultRepository(root_path / "output" / "results.json")

        try:
            repository = PostgreSQLResultRepository(database_url)
            logger.info("Persistencia PostgreSQL habilitada.")
            return repository
        except Exception as error:
            logger.warning(
                "No fue posible inicializar PostgreSQL; se usará persistencia mock.",
                backend=backend,
                error=str(error),
            )

    logger.info("Persistencia mock habilitada.", backend=backend)
    return MockResultRepository(root_path / "output" / "results.json")
