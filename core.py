from __future__ import annotations

from application.bootstrap import build_service_bundle


def analyze_value(value: str, enable_content_analysis: bool = False) -> dict[str, object]:
    services = build_service_bundle()
    domain_input = services.input_handler.prepare(
        value,
        source="manual",
        enable_content_analysis=enable_content_analysis,
    )
    return services.analysis_service.analyze(domain_input).to_dict()
