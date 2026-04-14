from __future__ import annotations

from io import BytesIO
from pathlib import Path

from application.bootstrap import ServiceBundle
from presentation.web_controller import create_app


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
