from __future__ import annotations

from pathlib import Path

import pytest

from application.alert_service import AlertService
from application.analysis_service import AnalysisService
from application.batch_monitor_service import BatchMonitorService
from application.brand_catalog_service import BrandCatalogService
from application.report_service import ReportService
from domain.explanation_builder import ExplanationBuilder
from domain.feature_extractor import FeatureExtractor
from domain.models import StaticContentSnapshot
from domain.risk_classifier import RiskClassifier
from domain.scoring_engine import ScoringEngine
from domain.url_domain_analyzer import URLDomainAnalyzer
from infrastructure.alert_publisher import InMemoryAlertPublisher
from infrastructure.catalog_provider_json import JSONCatalogProvider
from infrastructure.config_provider import ConfigProvider
from infrastructure.list_consolidator import ListConsolidator
from infrastructure.logging_monitoring import LoggingMonitoring
from infrastructure.report_writer import FileReportWriter
from infrastructure.result_repository import MockResultRepository
from infrastructure.zip_extractor import ZipExtractor
from presentation.input_handler import InputHandler


class FakeContentFetcher:
    def __init__(self, snapshot_factory=None) -> None:
        self._snapshot_factory = snapshot_factory or self._default_snapshot

    def fetch(self, url: str, timeout_seconds: float) -> StaticContentSnapshot:
        return self._snapshot_factory(url, timeout_seconds)

    @staticmethod
    def _default_snapshot(url: str, timeout_seconds: float) -> StaticContentSnapshot:
        return StaticContentSnapshot(
            requested_url=url,
            final_url=url,
            status_code=200,
            title="Contenido estático",
            text_excerpt="Página disponible para análisis.",
        )


@pytest.fixture
def base_path() -> Path:
    return Path(__file__).resolve().parent.parent


@pytest.fixture
def config_provider(base_path: Path) -> ConfigProvider:
    return ConfigProvider(base_path=base_path)


@pytest.fixture
def scoring_config(config_provider: ConfigProvider) -> dict[str, object]:
    return config_provider.load_scoring_config()


@pytest.fixture
def catalog_provider(config_provider: ConfigProvider) -> JSONCatalogProvider:
    return JSONCatalogProvider(config_provider)


@pytest.fixture
def brand_catalog_service(catalog_provider: JSONCatalogProvider) -> BrandCatalogService:
    return BrandCatalogService(catalog_provider)


@pytest.fixture
def input_handler() -> InputHandler:
    return InputHandler()


@pytest.fixture
def feature_extractor(scoring_config: dict[str, object]) -> FeatureExtractor:
    return FeatureExtractor(scoring_config)


@pytest.fixture
def scoring_engine(scoring_config: dict[str, object]) -> ScoringEngine:
    return ScoringEngine(scoring_config["rules"])


@pytest.fixture
def risk_classifier(scoring_config: dict[str, object]) -> RiskClassifier:
    return RiskClassifier(scoring_config["thresholds"])


@pytest.fixture
def analysis_factory(
    tmp_path: Path,
    brand_catalog_service: BrandCatalogService,
    feature_extractor: FeatureExtractor,
    scoring_engine: ScoringEngine,
    risk_classifier: RiskClassifier,
    scoring_config: dict[str, object],
):
    def _factory(snapshot_factory=None):
        logger = LoggingMonitoring(logger_name=f"phishing_col_tests_{tmp_path.name}")
        repository = MockResultRepository(tmp_path / "results.json")
        analysis_service = AnalysisService(
            brand_catalog_service=brand_catalog_service,
            url_domain_analyzer=URLDomainAnalyzer(
                feature_extractor, FakeContentFetcher(snapshot_factory)
            ),
            scoring_engine=scoring_engine,
            risk_classifier=risk_classifier,
            explanation_builder=ExplanationBuilder(),
            result_repository=repository,
            logger=logger,
        )
        alert_publisher = InMemoryAlertPublisher()
        alert_service = AlertService(
            alert_threshold=int(scoring_config["alert_threshold"]),
            publisher=alert_publisher,
        )
        report_service = ReportService(FileReportWriter())
        batch_service = BatchMonitorService(
            input_handler=InputHandler(),
            analysis_service=analysis_service,
            report_service=report_service,
            alert_service=alert_service,
            zip_extractor=ZipExtractor(),
            list_consolidator=ListConsolidator(),
            logger=logger,
        )
        return {
            "analysis_service": analysis_service,
            "batch_service": batch_service,
            "repository": repository,
            "alert_service": alert_service,
            "alert_publisher": alert_publisher,
            "input_handler": InputHandler(),
            "logger": logger,
        }

    return _factory
