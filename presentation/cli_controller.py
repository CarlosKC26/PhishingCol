from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from application.analysis_service import AnalysisService
from application.batch_monitor_service import BatchMonitorService
from presentation.input_handler import InputHandler, InputValidationError


class CLIController:
    def __init__(
        self,
        input_handler: InputHandler,
        analysis_service: AnalysisService,
        batch_monitor_service: BatchMonitorService,
    ) -> None:
        self._input_handler = input_handler
        self._analysis_service = analysis_service
        self._batch_monitor_service = batch_monitor_service

    def run(self, argv: list[str] | None = None) -> int:
        parser = self._build_parser()
        args = parser.parse_args(argv)
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        if args.batch:
            return self._run_batch(
                batch_paths=args.batch,
                output_dir=args.output_dir,
                enable_content_analysis=args.content_analysis,
                run_id=run_id,
            )

        input_value = args.input_value or self._prompt_input()
        if not input_value:
            parser.print_help()
            return 1

        try:
            domain_input = self._input_handler.prepare(
                input_value,
                source="manual",
                enable_content_analysis=args.content_analysis,
                run_id=run_id,
            )
        except InputValidationError as error:
            print(str(error))
            return 1

        result = self._analysis_service.analyze(domain_input)
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        return 0

    def _run_batch(
        self,
        batch_paths: list[str],
        output_dir: str,
        enable_content_analysis: bool,
        run_id: str,
    ) -> int:
        batch_result = self._batch_monitor_service.monitor_paths(
            batch_paths,
            output_dir=output_dir,
            run_id=run_id,
            enable_content_analysis=enable_content_analysis,
        )
        print(
            json.dumps(
                {
                    "results_count": len(batch_result["results"]),
                    "alerts": [alert.to_dict() for alert in batch_result["alerts"]],
                    "reports": batch_result["reports"],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    @staticmethod
    def _prompt_input() -> str:
        if not sys.stdin.isatty():
            return ""
        return input("Ingrese una URL o dominio a analizar: ").strip()

    @staticmethod
    def _build_parser() -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            description="Detección determinística de phishing basado en URLs y dominios."
        )
        parser.add_argument(
            "input_value",
            nargs="?",
            help="URL o dominio para análisis manual.",
        )
        parser.add_argument(
            "--batch",
            nargs="+",
            help="Rutas a archivos .txt o .zip para monitoreo batch.",
        )
        parser.add_argument(
            "--output-dir",
            default=str(Path("output")),
            help="Directorio de salida para resultados batch y persistencia mock.",
        )
        parser.add_argument(
            "--content-analysis",
            action="store_true",
            help="Activa el análisis opcional de contenido estático sin JavaScript.",
        )
        return parser
