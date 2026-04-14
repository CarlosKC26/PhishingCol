from __future__ import annotations

from domain.models import (
    AnalysisResult,
    ExplanationResult,
    FeatureSet,
    RiskLevel,
    ScoreResult,
)
from infrastructure.result_repository_postgresql import PostgreSQLResultRepository


class _FakeJsonb:
    def __init__(self, value):
        self.obj = value


class _FakeJsonModule:
    Jsonb = _FakeJsonb


class _FakeTypes:
    json = _FakeJsonModule()


class _FakePsycopg:
    types = _FakeTypes()


def test_build_insert_payload_wraps_jsonb_fields():
    repository = PostgreSQLResultRepository.__new__(PostgreSQLResultRepository)
    repository._psycopg = _FakePsycopg()

    result = AnalysisResult(
        input_value="banc0lombia-verificacion.xyz",
        normalized_domain="banc0lombia-verificacion.xyz",
        risk_level=RiskLevel.HIGH,
        score=74,
        status="complete",
        score_breakdown=ScoreResult(total_score=74, matched_rules=()),
        explanation=ExplanationResult(
            score=74,
            risk_level=RiskLevel.HIGH,
            triggered_rules=(),
            evidence=("evidencia",),
            limitations=(),
            summary="Resultado HIGH.",
        ),
        features=FeatureSet(
            normalized_url="https://banc0lombia-verificacion.xyz",
            normalized_domain="banc0lombia-verificacion.xyz",
            registrable_domain="banc0lombia-verificacion.xyz",
            tld="xyz",
            domain_length=28,
            url_length=36,
        ),
        matched_brands=("bancolombia",),
        limitations=(),
        errors=(),
        execution_time_ms=5,
        run_id="test",
    )

    payload = repository._build_insert_payload(result)

    assert isinstance(payload["matched_brands"], _FakeJsonb)
    assert payload["matched_brands"].obj == ["bancolombia"]
    assert isinstance(payload["limitations"], _FakeJsonb)
    assert isinstance(payload["errors"], _FakeJsonb)
    assert isinstance(payload["result_payload"], _FakeJsonb)
    assert payload["result_payload"].obj["risk_level"] == "HIGH"
