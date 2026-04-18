from __future__ import annotations

from application.interfaces import AISummaryGenerator
from domain.models import AISummaryResult, AnalysisResult
from infrastructure.logging_monitoring import LoggingMonitoring


class AISummaryService:
    def __init__(
        self,
        generator: AISummaryGenerator | None,
        logger: LoggingMonitoring,
    ) -> None:
        self._generator = generator
        self._logger = logger

    @property
    def is_available(self) -> bool:
        return self._generator is not None

    def summarize(self, result: AnalysisResult) -> AISummaryResult | None:
        if self._generator is None:
            return None

        try:
            summary = self._generator.generate(result)
        except Exception as error:
            self._logger.warning(
                "No fue posible generar el resumen asistido por IA",
                normalized_domain=result.normalized_domain,
                error_type=type(error).__name__,
            )
            return None

        self._logger.info(
            "Resumen asistido por IA generado",
            normalized_domain=result.normalized_domain,
            provider=summary.provider,
            model=summary.model,
        )
        return summary
