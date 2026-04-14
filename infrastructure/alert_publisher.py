from __future__ import annotations

from domain.models import AlertDraft


class InMemoryAlertPublisher:
    def __init__(self) -> None:
        self._alerts: list[AlertDraft] = []

    def publish(self, alert: AlertDraft) -> None:
        self._alerts.append(alert)

    @property
    def alerts(self) -> list[AlertDraft]:
        return list(self._alerts)
