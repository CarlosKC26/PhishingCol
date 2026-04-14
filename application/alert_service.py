from __future__ import annotations

from typing import Sequence

from application.interfaces import AlertPublisher
from domain.models import AlertDraft, AnalysisResult, RiskLevel


class AlertService:
    def __init__(self, alert_threshold: int, publisher: AlertPublisher | None = None) -> None:
        self._alert_threshold = alert_threshold
        self._publisher = publisher

    def build_alerts(self, results: Sequence[AnalysisResult]) -> list[AlertDraft]:
        alerts: list[AlertDraft] = []
        for result in results:
            if result.risk_level != RiskLevel.HIGH or result.score < self._alert_threshold:
                continue
            alert = AlertDraft(
                input_value=result.input_value,
                normalized_domain=result.normalized_domain,
                score=result.score,
                risk_level=result.risk_level,
                matched_brands=result.matched_brands,
                message=(
                    f"Dominio priorizado para revisión: {result.normalized_domain} "
                    f"(riesgo {result.risk_level.value}, score {result.score})."
                ),
            )
            alerts.append(alert)
            if self._publisher is not None:
                self._publisher.publish(alert)
        return alerts
