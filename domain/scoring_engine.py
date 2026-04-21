from __future__ import annotations

from collections.abc import Callable

from domain.models import FeatureSet, RuleConfig, RuleMatch, ScoreResult


RuleEvaluator = Callable[[RuleConfig, FeatureSet], tuple[bool, tuple[str, ...]]]


class ScoringEngine:
    def __init__(self, rules: tuple[RuleConfig, ...]) -> None:
        self._rules = rules
        self._evaluators: dict[str, RuleEvaluator] = {
            "typosquatting_detected": self._evaluate_typosquatting,
            "brand_keyword_detected": self._evaluate_brand_keywords,
            "brand_stuffing_detected": self._evaluate_brand_stuffing,
            "social_engineering_detected": self._evaluate_social_engineering,
            "suspicious_tld_detected": self._evaluate_suspicious_tld,
            "deceptive_subdomain_detected": self._evaluate_deceptive_subdomain,
            "anomalous_length_detected": self._evaluate_anomalous_length,
            "content_brand_detected": self._evaluate_content_brand,
        }

    def score(self, features: FeatureSet) -> ScoreResult:
        total_score = 0
        matched_rules: list[RuleMatch] = []

        for rule in self._rules:
            if not rule.enabled:
                continue

            evaluator = self._evaluators.get(rule.condition)
            if evaluator is None:
                continue

            matched, evidence = evaluator(rule, features)
            if not matched:
                continue

            total_score += rule.weight
            matched_rules.append(
                RuleMatch(
                    rule_id=rule.rule_id,
                    name=rule.name,
                    condition=rule.condition,
                    weight=rule.weight,
                    evidence=evidence,
                    references=rule.references,
                )
            )

        return ScoreResult(total_score=total_score, matched_rules=tuple(matched_rules))

    @staticmethod
    def _evaluate_typosquatting(
        rule: RuleConfig, features: FeatureSet
    ) -> tuple[bool, tuple[str, ...]]:
        if features.exact_brand_match or not features.typosquatting_matches:
            return False, ()
        return True, tuple(features.typosquatting_matches)

    @staticmethod
    def _evaluate_brand_keywords(
        rule: RuleConfig, features: FeatureSet
    ) -> tuple[bool, tuple[str, ...]]:
        if features.exact_brand_match or not features.matched_primary_keywords:
            return False, ()
        return True, tuple(features.matched_primary_keywords)

    @staticmethod
    def _evaluate_brand_stuffing(
        rule: RuleConfig, features: FeatureSet
    ) -> tuple[bool, tuple[str, ...]]:
        if features.exact_brand_match or not features.brand_stuffing_matches:
            return False, ()
        return True, tuple(features.brand_stuffing_matches)

    @staticmethod
    def _evaluate_social_engineering(
        rule: RuleConfig, features: FeatureSet
    ) -> tuple[bool, tuple[str, ...]]:
        if not features.social_engineering_terms:
            return False, ()
        return True, tuple(features.social_engineering_terms)

    @staticmethod
    def _evaluate_suspicious_tld(
        rule: RuleConfig, features: FeatureSet
    ) -> tuple[bool, tuple[str, ...]]:
        if not features.suspicious_tld:
            return False, ()
        return True, (features.tld,)

    @staticmethod
    def _evaluate_deceptive_subdomain(
        rule: RuleConfig, features: FeatureSet
    ) -> tuple[bool, tuple[str, ...]]:
        if not features.deceptive_subdomain:
            return False, ()
        evidence = tuple(features.suspicious_subdomain_tokens) or tuple(features.subdomains)
        return True, evidence

    @staticmethod
    def _evaluate_anomalous_length(
        rule: RuleConfig, features: FeatureSet
    ) -> tuple[bool, tuple[str, ...]]:
        if not features.anomalous_length:
            return False, ()
        return True, (str(features.domain_length),)

    @staticmethod
    def _evaluate_content_brand(
        rule: RuleConfig, features: FeatureSet
    ) -> tuple[bool, tuple[str, ...]]:
        if not features.content_brand_mentions or features.exact_brand_match:
            return False, ()
        return True, tuple(features.content_brand_mentions)
