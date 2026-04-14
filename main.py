from __future__ import annotations

import sys
from pathlib import Path

from application.alert_service import AlertService
from application.analysis_service import AnalysisService
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
from infrastructure.report_writer import FileReportWriter
from infrastructure.result_repository import MockResultRepository
from infrastructure.zip_extractor import ZipExtractor
from presentation.cli_controller import CLIController
from presentation.input_handler import InputHandler


def build_cli_controller(base_path: Path | None = None) -> CLIController:
    root_path = base_path or Path(__file__).resolve().parent
    config_provider = ConfigProvider(base_path=root_path)
    scoring_config = config_provider.load_scoring_config()
    input_handler = InputHandler(
        analysis_timeout_seconds=float(scoring_config["analysis_timeout_seconds"]),
        content_timeout_seconds=float(scoring_config["content_timeout_seconds"]),
    )

    logger = LoggingMonitoring(log_dir=root_path / "logs")
    catalog_provider = JSONCatalogProvider(config_provider)
    brand_catalog_service = BrandCatalogService(catalog_provider)
    feature_extractor = FeatureExtractor(scoring_config)
    url_domain_analyzer = URLDomainAnalyzer(feature_extractor, StaticContentFetcher())
    scoring_engine = ScoringEngine(scoring_config["rules"])
    risk_classifier = RiskClassifier(scoring_config["thresholds"])
    explanation_builder = ExplanationBuilder()
    result_repository = MockResultRepository(root_path / "output" / "results.json")
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
    return CLIController(input_handler, analysis_service, batch_monitor_service)


def main(argv: list[str] | None = None) -> int:
    controller = build_cli_controller()
    return controller.run(argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
