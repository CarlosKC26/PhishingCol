from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from application.alert_service import AlertService
from application.analysis_service import AnalysisService
from application.ai_summary_service import AISummaryService
from application.batch_monitor_service import BatchMonitorService
from application.brand_catalog_service import BrandCatalogService
from application.report_service import ReportService
from domain.explanation_builder import ExplanationBuilder
from domain.feature_extractor import FeatureExtractor
from domain.risk_classifier import RiskClassifier
from domain.scoring_engine import ScoringEngine
from domain.url_domain_analyzer import URLDomainAnalyzer
from infrastructure.alert_publisher import InMemoryAlertPublisher
from infrastructure.catalog_provider_json import JSONCatalogProvider
from infrastructure.config_provider import ConfigProvider
from infrastructure.content_fetcher import StaticContentFetcher
from infrastructure.list_consolidator import ListConsolidator
from infrastructure.logging_monitoring import LoggingMonitoring
from infrastructure.openrouter_client import OpenRouterClient
from infrastructure.openrouter_summary_generator import OpenRouterSummaryGenerator
from infrastructure.report_writer import FileReportWriter
from infrastructure.repository_factory import build_result_repository
from infrastructure.zip_extractor import ZipExtractor
from presentation.input_handler import InputHandler


@dataclass(frozen=True)
class ServiceBundle:
    input_handler: InputHandler
    analysis_service: AnalysisService
    batch_monitor_service: BatchMonitorService
    result_repository: object
    logger: LoggingMonitoring
    root_path: Path
    ai_summary_service: AISummaryService | None = None


def build_service_bundle(base_path: Path | None = None) -> ServiceBundle:
    root_path = base_path or Path(__file__).resolve().parent.parent
    _load_env_file(root_path / ".env")
    config_provider = ConfigProvider(base_path=root_path)
    scoring_config = config_provider.load_scoring_config()
    input_handler = InputHandler(
        analysis_timeout_seconds=float(scoring_config["analysis_timeout_seconds"]),
        content_timeout_seconds=float(scoring_config["content_timeout_seconds"]),
    )

    logger = LoggingMonitoring(log_dir=root_path / "logs")
    ai_summary_service = AISummaryService(
        generator=_build_ai_summary_generator(),
        logger=logger,
    )
    catalog_provider = JSONCatalogProvider(config_provider)
    brand_catalog_service = BrandCatalogService(catalog_provider)
    feature_extractor = FeatureExtractor(scoring_config)
    url_domain_analyzer = URLDomainAnalyzer(feature_extractor, StaticContentFetcher())
    scoring_engine = ScoringEngine(scoring_config["rules"])
    risk_classifier = RiskClassifier(scoring_config["thresholds"])
    explanation_builder = ExplanationBuilder()
    result_repository = build_result_repository(root_path, logger)
    analysis_service = AnalysisService(
        brand_catalog_service=brand_catalog_service,
        url_domain_analyzer=url_domain_analyzer,
        scoring_engine=scoring_engine,
        risk_classifier=risk_classifier,
        explanation_builder=explanation_builder,
        result_repository=result_repository,
        logger=logger,
    )
    report_service = ReportService(FileReportWriter())
    alert_service = AlertService(
        alert_threshold=int(scoring_config["alert_threshold"]),
        publisher=InMemoryAlertPublisher(),
    )
    batch_monitor_service = BatchMonitorService(
        input_handler=input_handler,
        analysis_service=analysis_service,
        report_service=report_service,
        alert_service=alert_service,
        zip_extractor=ZipExtractor(),
        list_consolidator=ListConsolidator(),
        logger=logger,
    )
    return ServiceBundle(
        input_handler=input_handler,
        analysis_service=analysis_service,
        batch_monitor_service=batch_monitor_service,
        result_repository=result_repository,
        logger=logger,
        root_path=root_path,
        ai_summary_service=ai_summary_service,
    )


def _build_ai_summary_generator() -> OpenRouterSummaryGenerator | None:
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        return None

    model = os.getenv("OPENROUTER_MODEL", "").strip()
    base_url = os.getenv(
        "OPENROUTER_API_BASE_URL",
        "https://openrouter.ai/api/v1/chat/completions",
    ).strip()
    timeout_seconds = float(os.getenv("OPENROUTER_TIMEOUT_SECONDS", "20"))
    app_referer = os.getenv("OPENROUTER_REFERER", "").strip()
    app_title = os.getenv("OPENROUTER_APP_TITLE", "PhishingCol").strip() or "PhishingCol"

    client = OpenRouterClient(
        api_key=api_key,
        base_url=base_url,
        timeout_seconds=timeout_seconds,
        app_referer=app_referer,
        app_title=app_title,
    )
    return OpenRouterSummaryGenerator(client=client, model=model)


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))
