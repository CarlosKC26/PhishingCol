from __future__ import annotations

from collections import Counter
from typing import Sequence

from application.interfaces import ReportWriter
from domain.models import AnalysisResult


class ReportService:
    def __init__(self, report_writer: ReportWriter) -> None:
        self._report_writer = report_writer

    def build_summary(self, results: Sequence[AnalysisResult]) -> dict[str, object]:
        risk_counter = Counter(result.risk_level.value for result in results)
        return {
            "total_results": len(results),
            "by_risk_level": dict(risk_counter),
            "high_risk_domains": [
                result.normalized_domain
                for result in results
                if result.risk_level.value == "HIGH"
            ],
        }

    def generate_reports(
        self, results: Sequence[AnalysisResult], output_dir: str, run_id: str
    ) -> dict[str, str]:
        summary = self.build_summary(results)
        return {
            "tabular_report": self._report_writer.write_tabular_report(
                results, output_dir, f"report_{run_id}.csv"
            ),
            "summary_report": self._report_writer.write_summary(
                summary, output_dir, f"summary_{run_id}.json"
            ),
            "export_report": self._report_writer.write_export(
                results, output_dir, f"results_{run_id}.json", "json"
            ),
        }
