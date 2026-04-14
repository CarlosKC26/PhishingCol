from __future__ import annotations

import json
from typing import Any

from domain.models import AnalysisResult, RiskLevel


class PostgreSQLResultRepository:
    def __init__(self, database_url: str) -> None:
        try:
            import psycopg
        except ImportError as error:
            raise RuntimeError(
                "psycopg no está instalado. Instale las dependencias para usar PostgreSQL."
            ) from error

        self._psycopg = psycopg
        self._database_url = database_url
        self._initialize_schema()

    def save(self, result: AnalysisResult) -> None:
        payload = self._build_insert_payload(result)
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO analysis_results (
                        run_id,
                        input_value,
                        normalized_domain,
                        risk_level,
                        score,
                        status,
                        matched_brands,
                        limitations,
                        errors,
                        execution_time_ms,
                        analyzed_at,
                        result_payload
                    ) VALUES (
                        %(run_id)s,
                        %(input_value)s,
                        %(normalized_domain)s,
                        %(risk_level)s,
                        %(score)s,
                        %(status)s,
                        %(matched_brands)s,
                        %(limitations)s,
                        %(errors)s,
                        %(execution_time_ms)s,
                        %(analyzed_at)s,
                        %(result_payload)s
                    )
                    """,
                    payload,
                )
            connection.commit()

    def find_by_execution(self, run_id: str) -> list[AnalysisResult]:
        rows = self._fetch_all(
            """
            SELECT result_payload
            FROM analysis_results
            WHERE run_id = %s
            ORDER BY analyzed_at ASC
            """,
            (run_id,),
        )
        return [self._deserialize_result(row[0]) for row in rows]

    def find_high_risk(self) -> list[AnalysisResult]:
        rows = self._fetch_all(
            """
            SELECT result_payload
            FROM analysis_results
            WHERE risk_level = %s
            ORDER BY analyzed_at DESC
            """,
            (RiskLevel.HIGH.value,),
        )
        return [self._deserialize_result(row[0]) for row in rows]

    def _fetch_all(self, query: str, params: tuple[Any, ...]) -> list[tuple[Any, ...]]:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()

    def _connect(self):
        return self._psycopg.connect(self._database_url)

    def _build_insert_payload(self, result: AnalysisResult) -> dict[str, Any]:
        jsonb = self._psycopg.types.json.Jsonb
        return {
            "run_id": result.run_id,
            "input_value": result.input_value,
            "normalized_domain": result.normalized_domain,
            "risk_level": result.risk_level.value,
            "score": result.score,
            "status": result.status,
            "matched_brands": jsonb(list(result.matched_brands)),
            "limitations": jsonb(list(result.limitations)),
            "errors": jsonb(list(result.errors)),
            "execution_time_ms": result.execution_time_ms,
            "analyzed_at": result.analyzed_at,
            "result_payload": jsonb(result.to_dict()),
        }

    def _initialize_schema(self) -> None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS analysis_results (
                        id BIGSERIAL PRIMARY KEY,
                        run_id TEXT NOT NULL,
                        input_value TEXT NOT NULL,
                        normalized_domain TEXT NOT NULL,
                        risk_level TEXT NOT NULL,
                        score INTEGER NOT NULL,
                        status TEXT NOT NULL,
                        matched_brands JSONB NOT NULL DEFAULT '[]'::jsonb,
                        limitations JSONB NOT NULL DEFAULT '[]'::jsonb,
                        errors JSONB NOT NULL DEFAULT '[]'::jsonb,
                        execution_time_ms INTEGER NOT NULL,
                        analyzed_at TIMESTAMPTZ NOT NULL,
                        result_payload JSONB NOT NULL
                    );
                    CREATE INDEX IF NOT EXISTS idx_analysis_results_run_id
                        ON analysis_results(run_id);
                    CREATE INDEX IF NOT EXISTS idx_analysis_results_risk_level
                        ON analysis_results(risk_level);
                    """
                )
            connection.commit()

    @staticmethod
    def _deserialize_result(payload: dict[str, Any] | str) -> AnalysisResult:
        if isinstance(payload, str):
            data = json.loads(payload)
        else:
            data = payload

        from domain.models import AnalysisResult, ExplanationResult, FeatureSet, RiskLevel, RuleMatch, ScoreResult

        matched_rules = tuple(
            RuleMatch(
                rule_id=rule["rule_id"],
                name=rule["name"],
                condition=rule["condition"],
                weight=rule["weight"],
                evidence=tuple(rule.get("evidence", [])),
                references=tuple(rule.get("references", [])),
            )
            for rule in data["score_breakdown"]["matched_rules"]
        )
        features = FeatureSet(**data["features"])
        explanation = ExplanationResult(
            score=data["explanation"]["score"],
            risk_level=RiskLevel(data["explanation"]["risk_level"]),
            triggered_rules=matched_rules,
            evidence=tuple(data["explanation"]["evidence"]),
            limitations=tuple(data["explanation"]["limitations"]),
            summary=data["explanation"]["summary"],
        )
        return AnalysisResult(
            input_value=data["input_value"],
            normalized_domain=data["normalized_domain"],
            risk_level=RiskLevel(data["risk_level"]),
            score=data["score"],
            status=data["status"],
            score_breakdown=ScoreResult(
                total_score=data["score_breakdown"]["total_score"],
                matched_rules=matched_rules,
            ),
            explanation=explanation,
            features=features,
            matched_brands=tuple(data.get("matched_brands", [])),
            limitations=tuple(data.get("limitations", [])),
            errors=tuple(data.get("errors", [])),
            execution_time_ms=data.get("execution_time_ms", 0),
            analyzed_at=data.get("analyzed_at", ""),
            run_id=data.get("run_id", "manual"),
        )
