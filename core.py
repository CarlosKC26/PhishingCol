from __future__ import annotations

from pathlib import Path

from main import build_cli_controller


def analyze_value(value: str, enable_content_analysis: bool = False) -> dict[str, object]:
    controller = build_cli_controller(Path(__file__).resolve().parent)
    domain_input = controller._input_handler.prepare(  # noqa: SLF001
        value,
        source="manual",
        enable_content_analysis=enable_content_analysis,
    )
    return controller._analysis_service.analyze(domain_input).to_dict()  # noqa: SLF001
