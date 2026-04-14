from __future__ import annotations

from domain.models import FeatureSet, RiskLevel, ScoreResult


def _base_features() -> FeatureSet:
    return FeatureSet(
        normalized_url="https://example.com",
        normalized_domain="example.com",
        registrable_domain="example.com",
        tld="com",
        domain_length=11,
        url_length=19,
    )


def test_classifies_high_medium_and_low(risk_classifier):
    features = _base_features()

    assert risk_classifier.classify(ScoreResult(80, ()), features) == RiskLevel.HIGH
    assert risk_classifier.classify(ScoreResult(45, ()), features) == RiskLevel.MEDIUM
    assert risk_classifier.classify(ScoreResult(10, ()), features) == RiskLevel.LOW


def test_classifies_unknown_when_only_errors_exist(risk_classifier):
    features = _base_features()
    features.errors.append("HTTP_TIMEOUT")

    assert risk_classifier.classify(ScoreResult(0, ()), features) == RiskLevel.UNKNOWN
