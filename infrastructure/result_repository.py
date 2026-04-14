from __future__ import annotations

import json
from pathlib import Path

from domain.models import AnalysisResult, RiskLevel


class MockResultRepository:
    def __init__(self, storage_path: str | Path | None = None) -> None:
        self._storage_path = Path(storage_path) if storage_path else None
        self._results: list[AnalysisResult] = []

    def save(self, result: AnalysisResult) -> None:
        self._results.append(result)
        if self._storage_path is None:
            return
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        with self._storage_path.open("w", encoding="utf-8") as file_handle:
            json.dump(
                [analysis_result.to_dict() for analysis_result in self._results],
                file_handle,
                ensure_ascii=False,
                indent=2,
            )

    def find_by_execution(self, run_id: str) -> list[AnalysisResult]:
        return [result for result in self._results if result.run_id == run_id]

    def find_high_risk(self) -> list[AnalysisResult]:
        return [
            result
            for result in self._results
            if result.risk_level == RiskLevel.HIGH
        ]

    @property
    def results(self) -> list[AnalysisResult]:
        return list(self._results)
