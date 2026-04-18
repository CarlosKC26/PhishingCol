from __future__ import annotations

from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from flask import Flask, render_template, request
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from application.bootstrap import ServiceBundle
from domain.models import AnalysisResult
from presentation.input_handler import InputValidationError


def create_app(services: ServiceBundle) -> Flask:
    app = Flask(
        __name__,
        template_folder=str(services.root_path / "presentation" / "templates"),
    )
    app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

    @app.get("/")
    def index():
        return _render_home(services)

    @app.post("/analyze")
    def analyze():
        input_value = request.form.get("input_value", "").strip()
        enable_content_analysis = request.form.get("content_analysis") == "on"
        enable_ai_summary = request.form.get("ai_summary") == "on"

        try:
            domain_input = services.input_handler.prepare(
                input_value,
                source="web",
                enable_content_analysis=enable_content_analysis,
                run_id=datetime.now().strftime("%Y%m%d_%H%M%S"),
            )
            result = services.analysis_service.analyze(domain_input)
            ai_summary, ai_error_message = _build_ai_summary(
                services=services,
                result=result,
                requested=enable_ai_summary,
            )
            return _render_home(
                services,
                result=result.to_dict(),
                input_value=input_value,
                ai_summary=ai_summary,
                ai_error_message=ai_error_message,
                ai_summary_requested=enable_ai_summary,
            )
        except InputValidationError as error:
            return (
                _render_home(
                    services,
                    result=None,
                    input_value=input_value,
                    error_message=str(error),
                    ai_summary_requested=enable_ai_summary,
                ),
                400,
            )

    @app.post("/batch")
    def batch():
        batch_text = request.form.get("batch_text", "").strip()
        enable_content_analysis = request.form.get("batch_content_analysis") == "on"
        uploaded_files = request.files.getlist("batch_files")

        try:
            batch_result = _run_batch_analysis(
                services=services,
                uploaded_files=uploaded_files,
                batch_text=batch_text,
                enable_content_analysis=enable_content_analysis,
            )
            return _render_home(
                services,
                batch_result=batch_result,
                batch_text=batch_text,
            )
        except ValueError as error:
            return (
                _render_home(
                    services,
                    batch_result=None,
                    batch_text=batch_text,
                    batch_error_message=str(error),
                ),
                400,
            )

    return app


def _render_home(
    services: ServiceBundle,
    result: dict[str, object] | None = None,
    input_value: str = "",
    error_message: str | None = None,
    ai_summary: dict[str, object] | None = None,
    ai_error_message: str | None = None,
    ai_summary_requested: bool = False,
    batch_result: dict[str, object] | None = None,
    batch_text: str = "",
    batch_error_message: str | None = None,
):
    recent_high_risk = _safe_find_high_risk(services)[:5]
    return render_template(
        "index.html",
        page_title="PhishingCol",
        result=result,
        input_value=input_value,
        error_message=error_message,
        ai_summary=ai_summary,
        ai_error_message=ai_error_message,
        ai_summary_requested=ai_summary_requested,
        ai_summary_available=_ai_summary_available(services),
        batch_result=batch_result,
        batch_text=batch_text,
        batch_error_message=batch_error_message,
        recent_high_risk=recent_high_risk,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )


def _run_batch_analysis(
    services: ServiceBundle,
    uploaded_files: list[FileStorage],
    batch_text: str,
    enable_content_analysis: bool,
) -> dict[str, object]:
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = services.root_path / "output" / "web_batch" / run_id
    file_paths: list[str] = []

    with TemporaryDirectory() as temporary_dir:
        temporary_root = Path(temporary_dir)
        if batch_text:
            text_path = temporary_root / "batch_input.txt"
            cleaned_lines = [
                line.strip()
                for line in batch_text.splitlines()
                if line.strip()
            ]
            text_path.write_text("\n".join(cleaned_lines), encoding="utf-8")
            file_paths.append(str(text_path))

        for uploaded_file in uploaded_files:
            if uploaded_file is None or not uploaded_file.filename:
                continue
            filename = secure_filename(uploaded_file.filename)
            suffix = Path(filename).suffix.lower()
            if suffix not in {".txt", ".zip"}:
                raise ValueError("Solo se permiten archivos .txt o .zip para el monitoreo batch.")
            destination = temporary_root / filename
            uploaded_file.save(destination)
            file_paths.append(str(destination))

        if not file_paths:
            raise ValueError(
                "Debe cargar al menos un archivo .txt/.zip o pegar una lista de dominios."
            )

        raw_result = services.batch_monitor_service.monitor_paths(
            file_paths=file_paths,
            output_dir=str(output_dir),
            run_id=run_id,
            enable_content_analysis=enable_content_analysis,
        )

    serialized_results = [result.to_dict() for result in raw_result["results"]]
    high_risk_results = [
        item for item in serialized_results if item["risk_level"] == "HIGH"
    ][:10]
    return {
        "run_id": run_id,
        "results_count": len(serialized_results),
        "high_risk_count": len(
            [item for item in serialized_results if item["risk_level"] == "HIGH"]
        ),
        "alerts": [alert.to_dict() for alert in raw_result["alerts"]],
        "reports": raw_result["reports"],
        "high_risk_results": high_risk_results,
    }


def _safe_find_high_risk(services: ServiceBundle) -> list[dict[str, object]]:
    repository = services.result_repository
    if not hasattr(repository, "find_high_risk"):
        return []

    try:
        return [result.to_dict() for result in repository.find_high_risk()]
    except Exception:
        services.logger.warning(
            "No fue posible consultar los resultados de alto riesgo para la UI."
        )
        return []


def _ai_summary_available(services: ServiceBundle) -> bool:
    ai_summary_service = services.ai_summary_service
    if ai_summary_service is None:
        return False
    return ai_summary_service.is_available


def _build_ai_summary(
    services: ServiceBundle,
    result: AnalysisResult,
    requested: bool,
) -> tuple[dict[str, object] | None, str | None]:
    if not requested:
        return None, None

    ai_summary_service = services.ai_summary_service
    if ai_summary_service is None or not ai_summary_service.is_available:
        return (
            None,
            "El resumen asistido por IA no esta disponible. Configura OPENROUTER_API_KEY para activarlo.",
        )

    summary = ai_summary_service.summarize(result)
    if summary is None:
        return (
            None,
            "No fue posible generar el resumen asistido por IA para este analisis.",
        )
    return summary.to_dict(), None
