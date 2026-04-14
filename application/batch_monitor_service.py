from __future__ import annotations

from pathlib import Path
from typing import Sequence

from application.alert_service import AlertService
from application.analysis_service import AnalysisService
from application.report_service import ReportService
from infrastructure.list_consolidator import ListConsolidator
from infrastructure.logging_monitoring import LoggingMonitoring
from infrastructure.zip_extractor import ZipExtractor
from presentation.input_handler import InputHandler, InputValidationError


class BatchMonitorService:
    def __init__(
        self,
        input_handler: InputHandler,
        analysis_service: AnalysisService,
        report_service: ReportService,
        alert_service: AlertService,
        zip_extractor: ZipExtractor,
        list_consolidator: ListConsolidator,
        logger: LoggingMonitoring,
    ) -> None:
        self._input_handler = input_handler
        self._analysis_service = analysis_service
        self._report_service = report_service
        self._alert_service = alert_service
        self._zip_extractor = zip_extractor
        self._list_consolidator = list_consolidator
        self._logger = logger

    def monitor_paths(
        self,
        file_paths: Sequence[str],
        output_dir: str,
        run_id: str,
        enable_content_analysis: bool = False,
    ) -> dict[str, object]:
        txt_files: list[str] = []
        extract_dir = Path(output_dir) / "extracted"
        for file_path in file_paths:
            suffix = Path(file_path).suffix.lower()
            if suffix == ".txt":
                txt_files.append(file_path)
            elif suffix == ".zip":
                txt_files.extend(
                    [
                        candidate
                        for candidate in self._zip_extractor.extract(file_path, extract_dir)
                        if Path(candidate).suffix.lower() == ".txt"
                    ]
                )
            else:
                self._logger.warning("Archivo batch ignorado", file_path=file_path)

        domains = self._list_consolidator.consolidate(txt_files)
        results = []
        for domain in domains:
            try:
                input_data = self._input_handler.prepare(
                    domain,
                    source="batch",
                    enable_content_analysis=enable_content_analysis,
                    run_id=run_id,
                )
            except InputValidationError:
                self._logger.warning("Dominio batch inválido", domain=domain)
                continue
            results.append(self._analysis_service.analyze(input_data))

        reports = self._report_service.generate_reports(results, output_dir, run_id)
        alerts = self._alert_service.build_alerts(results)
        return {"results": results, "alerts": alerts, "reports": reports}
