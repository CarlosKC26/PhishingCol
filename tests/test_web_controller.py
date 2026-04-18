from __future__ import annotations

from io import BytesIO
from pathlib import Path

from application.bootstrap import ServiceBundle
from domain.models import AISummaryResult
from presentation.web_controller import create_app


class FakeAISummaryService:
    def __init__(self, available: bool = True) -> None:
        self._available = available

    @property
    def is_available(self) -> bool:
        return self._available

    def summarize(self, result):
        return AISummaryResult(
            narrative_summary="El dominio presenta multiples senales de riesgo y requiere validacion antes de interactuar con el sitio.",
            suggested_steps=(
                "No ingreses credenciales ni codigos de verificacion.",
                "Valida el dominio en el sitio oficial de la marca.",
                "Reporta el hallazgo al equipo de seguridad o a la entidad afectada.",
            ),
            disclaimer=(
                "Este resumen fue generado por inteligencia artificial a partir de los resultados deterministas del sistema."
            ),
            provider="OpenRouter",
            model="demo-model",
        )


def test_web_index_renders_landing_page(analysis_factory, tmp_path: Path):
    services = analysis_factory()
    app = create_app(
        ServiceBundle(
            input_handler=services["input_handler"],
            analysis_service=services["analysis_service"],
            batch_monitor_service=services["batch_service"],
            result_repository=services["repository"],
            logger=services["logger"],
            root_path=Path(__file__).resolve().parent.parent,
        )
    )

    response = app.test_client().get("/")

    assert response.status_code == 200
    assert b"PhishingCol" in response.data
    assert b"Consulta manual" in response.data


def test_web_analyze_returns_result_panel(analysis_factory, tmp_path: Path):
    services = analysis_factory()
    app = create_app(
        ServiceBundle(
            input_handler=services["input_handler"],
            analysis_service=services["analysis_service"],
            batch_monitor_service=services["batch_service"],
            result_repository=services["repository"],
            logger=services["logger"],
            root_path=Path(__file__).resolve().parent.parent,
        )
    )

    response = app.test_client().post(
        "/analyze",
        data={"input_value": "banc0lombia-verificacion.xyz"},
    )

    assert response.status_code == 200
    assert b"HIGH" in response.data
    assert b"RN-04" in response.data


def test_web_batch_returns_summary_panel(analysis_factory, tmp_path: Path):
    services = analysis_factory()
    app = create_app(
        ServiceBundle(
            input_handler=services["input_handler"],
            analysis_service=services["analysis_service"],
            batch_monitor_service=services["batch_service"],
            result_repository=services["repository"],
            logger=services["logger"],
            root_path=Path(__file__).resolve().parent.parent,
        )
    )

    response = app.test_client().post(
        "/batch",
        data={
            "batch_text": "banc0lombia-verificacion.xyz\nbancolombia.com.co",
            "batch_files": (BytesIO(b""), ""),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert b"Resultados procesados" in response.data
    assert b"Hallazgos HIGH" in response.data
    assert b"banc0lombia-verificacion.xyz" in response.data


def test_web_analyze_can_render_ai_summary_panel(analysis_factory, tmp_path: Path):
    services = analysis_factory()
    app = create_app(
        ServiceBundle(
            input_handler=services["input_handler"],
            analysis_service=services["analysis_service"],
            batch_monitor_service=services["batch_service"],
            result_repository=services["repository"],
            logger=services["logger"],
            root_path=Path(__file__).resolve().parent.parent,
            ai_summary_service=FakeAISummaryService(),
        )
    )

    response = app.test_client().post(
        "/analyze",
        data={"input_value": "banc0lombia-verificacion.xyz", "ai_summary": "on"},
    )

    assert response.status_code == 200
    assert b"Resumen narrativo asistido por IA" in response.data
    assert b"Pasos sugeridos" in response.data
    assert b"Disclaimer IA" in response.data


def test_web_analyze_shows_ai_unavailable_message(analysis_factory, tmp_path: Path):
    services = analysis_factory()
    app = create_app(
        ServiceBundle(
            input_handler=services["input_handler"],
            analysis_service=services["analysis_service"],
            batch_monitor_service=services["batch_service"],
            result_repository=services["repository"],
            logger=services["logger"],
            root_path=Path(__file__).resolve().parent.parent,
            ai_summary_service=FakeAISummaryService(available=False),
        )
    )

    response = app.test_client().post(
        "/analyze",
        data={"input_value": "banc0lombia-verificacion.xyz", "ai_summary": "on"},
    )

    assert response.status_code == 200
    assert b"OPENROUTER_API_KEY" in response.data
