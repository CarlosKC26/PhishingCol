from __future__ import annotations

from typing import Protocol, Sequence

from domain.models import (
    AlertDraft,
    AISummaryResult,
    AnalysisResult,
    BrandCatalog,
    BrandDefinition,
    DomainInput,
    StaticContentSnapshot,
)


class Analyzer(Protocol):
    def analyze(self, input_data: DomainInput) -> AnalysisResult:
        ...


class CatalogProvider(Protocol):
    def get_brands(self) -> BrandCatalog:
        ...

    def get_brand(self, brand_id: str) -> BrandDefinition | None:
        ...


class ResultStore(Protocol):
    def save(self, result: AnalysisResult) -> None:
        ...

    def find_by_execution(self, run_id: str) -> list[AnalysisResult]:
        ...

    def find_high_risk(self) -> list[AnalysisResult]:
        ...


class AlertPublisher(Protocol):
    def publish(self, alert: AlertDraft) -> None:
        ...


class ReportWriter(Protocol):
    def write_tabular_report(
        self, results: Sequence[AnalysisResult], destination_dir: str, file_name: str
    ) -> str:
        ...

    def write_summary(
        self, summary: dict[str, object], destination_dir: str, file_name: str
    ) -> str:
        ...

    def write_export(
        self,
        results: Sequence[AnalysisResult],
        destination_dir: str,
        file_name: str,
        format_name: str,
    ) -> str:
        ...


class StaticContentFetcherPort(Protocol):
    def fetch(self, url: str, timeout_seconds: float) -> StaticContentSnapshot:
        ...


class AISummaryGenerator(Protocol):
    def generate(self, result: AnalysisResult) -> AISummaryResult:
        ...
