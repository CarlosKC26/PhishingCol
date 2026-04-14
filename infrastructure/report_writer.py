from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Sequence

from domain.models import AnalysisResult


class FileReportWriter:
    def write_tabular_report(
        self, results: Sequence[AnalysisResult], destination_dir: str, file_name: str
    ) -> str:
        output_dir = Path(destination_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / file_name
        with output_path.open("w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(
                csv_file,
                fieldnames=[
                    "input_value",
                    "normalized_domain",
                    "risk_level",
                    "score",
                    "status",
                    "matched_brands",
                    "execution_time_ms",
                ],
            )
            writer.writeheader()
            for result in results:
                writer.writerow(
                    {
                        "input_value": result.input_value,
                        "normalized_domain": result.normalized_domain,
                        "risk_level": result.risk_level.value,
                        "score": result.score,
                        "status": result.status,
                        "matched_brands": ",".join(result.matched_brands),
                        "execution_time_ms": result.execution_time_ms,
                    }
                )
        return str(output_path)

    def write_summary(
        self, summary: dict[str, object], destination_dir: str, file_name: str
    ) -> str:
        output_dir = Path(destination_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / file_name
        with output_path.open("w", encoding="utf-8") as summary_file:
            json.dump(summary, summary_file, ensure_ascii=False, indent=2)
        return str(output_path)

    def write_export(
        self,
        results: Sequence[AnalysisResult],
        destination_dir: str,
        file_name: str,
        format_name: str,
    ) -> str:
        output_dir = Path(destination_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / file_name
        if format_name != "json":
            raise ValueError("Solo se soporta exportación JSON en este adaptador.")
        with output_path.open("w", encoding="utf-8") as export_file:
            json.dump(
                [result.to_dict() for result in results],
                export_file,
                ensure_ascii=False,
                indent=2,
            )
        return str(output_path)
