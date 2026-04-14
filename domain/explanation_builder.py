from __future__ import annotations

from domain.models import ExplanationResult, FeatureSet, RiskLevel, ScoreResult


class ExplanationBuilder:
    def build(
        self,
        score_result: ScoreResult,
        risk_level: RiskLevel,
        features: FeatureSet,
    ) -> ExplanationResult:
        triggered_rules = score_result.matched_rules
        evidence = tuple(dict.fromkeys(features.evidence))
        limitations = tuple(dict.fromkeys(features.limitations))
        rule_names = ", ".join(rule.rule_id for rule in triggered_rules) or "ninguna"
        summary = (
            f"Resultado {risk_level.value} con puntaje {score_result.total_score}. "
            f"Reglas activadas: {rule_names}."
        )
        if limitations:
            summary += " El análisis presenta limitaciones controladas."

        return ExplanationResult(
            score=score_result.total_score,
            risk_level=risk_level,
            triggered_rules=triggered_rules,
            evidence=evidence,
            limitations=limitations,
            summary=summary,
        )
