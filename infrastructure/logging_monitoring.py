from __future__ import annotations

import logging
from pathlib import Path


class LoggingMonitoring:
    def __init__(
        self,
        logger_name: str = "phishing_col",
        log_dir: str | Path | None = None,
    ) -> None:
        self._logger = logging.getLogger(logger_name)
        if self._logger.handlers:
            return

        self._logger.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )

        if log_dir is not None:
            output_dir = Path(log_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(output_dir / "phishing_col.log", "a")
            file_handler.setFormatter(formatter)
            self._logger.addHandler(file_handler)
            return

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        self._logger.addHandler(stream_handler)

    def info(self, message: str, **context: object) -> None:
        self._logger.info(self._format(message, context))

    def warning(self, message: str, **context: object) -> None:
        self._logger.warning(self._format(message, context))

    def error(self, message: str, **context: object) -> None:
        self._logger.error(self._format(message, context))

    @staticmethod
    def _format(message: str, context: dict[str, object]) -> str:
        if not context:
            return message
        serialized = ", ".join(f"{key}={value}" for key, value in context.items())
        return f"{message} | {serialized}"
