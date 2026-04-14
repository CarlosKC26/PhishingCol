from __future__ import annotations

from time import perf_counter

from application.brand_catalog_service import BrandCatalogService
from application.interfaces import ResultStore
from domain.explanation_builder import ExplanationBuilder
from domain.models import AnalysisResult, DomainInput, FeatureSet, RiskLevel, ScoreResult
from domain.risk_classifier import RiskClassifier
from domain.scoring_engine import ScoringEngine
from domain.url_domain_analyzer import URLDomainAnalyzer
from infrastructure.logging_monitoring import LoggingMonitoring


class AnalysisService:
    def __init__(
        self,
        brand_catalog_service: BrandCatalogService,
        url_domain_analyzer: URLDomainAnalyzer,
        scoring_engine: ScoringEngine,
        risk_classifier: RiskClassifier,
        explanation_builder: ExplanationBuilder,
        result_repository: ResultStore,
        logger: LoggingMonitoring,
    ) -> None:
        self._brand_catalog_service = brand_catalog_service
        self._url_domain_analyzer = url_domain_analyzer
        self._scoring_engine = scoring_engine
        self._risk_classifier = risk_classifier
        self._explanation_builder = explanation_builder
        self._result_repository = result_repository
        self._logger = logger

    def analyze(self, input_data: DomainInput) -> AnalysisResult:
        start = perf_counter()
        self._logger.info("Inicio de análisis", input_value=input_data.original_value)
        catalog = self._brand_catalog_service.get_catalog()

        try:
            features = self._url_domain_analyzer.analyze(input_data, catalog)
            score_result = self._scoring_engine.score(features)
            risk_level = self._risk_classifier.classify(score_result, features)
            explanation = self._explanation_builder.build(
                score_result, risk_level, features
            )
            status = "partial" if features.limitations or features.errors else "complete"
            result = AnalysisResult(
                input_value=input_data.original_value,
                normalized_domain=features.registrable_domain,
                risk_level=risk_level,
                score=score_result.total_score,
                status=status,
                score_breakdown=score_result,
                explanation=explanation,
                features=features,
                matched_brands=tuple(features.matched_brand_ids),
                limitations=tuple(features.limitations),
                errors=tuple(features.errors),
                execution_time_ms=int((perf_counter() - start) * 1000),
                run_id=input_data.run_id,
            )
        except Exception:
            fallback_features = FeatureSet(
                normalized_url=input_data.normalized_url,
                normalized_domain=input_data.normalized_domain,
                registrable_domain=input_data.normalized_domain,
                tld="",
                domain_length=len(input_data.normalized_domain),
                url_length=len(input_data.normalized_url),
                limitations=[
                    "Se produjo una limitación controlada durante el análisis; "
                    "se devolvió el mejor resultado disponible."
                ],
                errors=["ANALYSIS_PARTIAL"],
            )
            score_result = ScoreResult(total_score=0, matched_rules=())
            risk_level = RiskLevel.UNKNOWN
            explanation = self._explanation_builder.build(
                score_result, risk_level, fallback_features
            )
            result = AnalysisResult(
                input_value=input_data.original_value,
                normalized_domain=input_data.normalized_domain,
                risk_level=risk_level,
                score=0,
                status="partial",
                score_breakdown=score_result,
                explanation=explanation,
                features=fallback_features,
                limitations=tuple(fallback_features.limitations),
                errors=tuple(fallback_features.errors),
                execution_time_ms=int((perf_counter() - start) * 1000),
                run_id=input_data.run_id,
            )
            self._logger.error(
                "Fallo controlado durante el análisis",
                input_value=input_data.original_value,
            )

        self._result_repository.save(result)
        self._logger.info(
            "Fin de análisis",
            normalized_domain=result.normalized_domain,
            risk_level=result.risk_level.value,
            score=result.score,
            execution_time_ms=result.execution_time_ms,
        )
        return result
