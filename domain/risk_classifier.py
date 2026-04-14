from __future__ import annotations

from domain.models import FeatureSet, RiskLevel, ScoreResult


class RiskClassifier:
    def __init__(self, thresholds: dict[str, object]) -> None:
        self._medium_threshold = int(thresholds.get("medium", 40))
        self._high_threshold = int(thresholds.get("high", 70))
        self._unknown_on_errors = bool(thresholds.get("unknown_on_errors", True))

    def classify(self, score_result: ScoreResult, features: FeatureSet) -> RiskLevel:
        if (
            self._unknown_on_errors
            and features.errors
            and score_result.total_score == 0
            and not features.has_structural_signal()
        ):
            return RiskLevel.UNKNOWN

        if score_result.total_score >= self._high_threshold:
            return RiskLevel.HIGH
        if score_result.total_score >= self._medium_threshold:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW
