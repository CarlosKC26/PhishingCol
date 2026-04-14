from __future__ import annotations

from pathlib import Path

from domain.models import RiskLevel, StaticContentSnapshot


def test_pipeline_legitimate_url_returns_low_risk(analysis_factory, input_handler):
    services = analysis_factory(
        lambda url, timeout: StaticContentSnapshot(
            requested_url=url,
            final_url=url,
            status_code=200,
            title="Bancolombia Personas",
            text_excerpt="Portal oficial Bancolombia.",
        )
    )
    input_data = input_handler.prepare("https://bancolombia.com.co/personas")

    result = services["analysis_service"].analyze(input_data)

    assert result.risk_level == RiskLevel.LOW
    assert result.score == 0
    assert result.status == "complete"
    assert result.explanation.score == 0


def test_pipeline_typosquatting_reaches_high_risk(analysis_factory, input_handler):
    services = analysis_factory(
        lambda url, timeout: StaticContentSnapshot(
            requested_url=url,
            final_url=url,
            status_code=200,
            title="Bancolombia seguridad",
            text_excerpt="Ingrese su clave para verificar el acceso.",
        )
    )
    input_data = input_handler.prepare("https://banc0lombia-verificacion.xyz/login")

    result = services["analysis_service"].analyze(input_data)
    rule_ids = {rule.rule_id for rule in result.score_breakdown.matched_rules}

    assert result.risk_level == RiskLevel.HIGH
    assert {"RN-04", "RN-05", "RN-07", "RN-10", "RN-11"} <= rule_ids
    assert result.status == "complete"


def test_pipeline_keywords_case_reaches_medium_risk(analysis_factory, input_handler):
    services = analysis_factory()
    input_data = input_handler.prepare(
        "https://davivienda-validacion-pago-click.top/login"
    )

    result = services["analysis_service"].analyze(input_data)

    assert result.risk_level in {RiskLevel.MEDIUM, RiskLevel.HIGH}
    assert result.score >= 40


def test_pipeline_long_domain_is_flagged(analysis_factory, input_handler):
    services = analysis_factory()
    input_data = input_handler.prepare(
        "https://actualizar-seguridad-bloqueo-clientes.nequi-promocion-ayuda-secure-login.top"
    )

    result = services["analysis_service"].analyze(input_data)
    rule_ids = {rule.rule_id for rule in result.score_breakdown.matched_rules}

    assert "RN-09" in rule_ids
    assert result.risk_level in {RiskLevel.MEDIUM, RiskLevel.HIGH}


def test_pipeline_http_error_returns_partial_result(analysis_factory, input_handler):
    services = analysis_factory(
        lambda url, timeout: StaticContentSnapshot(
            requested_url=url,
            status_code=None,
            error_code="HTTP_TIMEOUT",
            limitation="El análisis de contenido excedió el tiempo; se devolvió un análisis parcial."
        )
    )
    input_data = input_handler.prepare("https://nequi-verificacion.xyz/login")

    result = services["analysis_service"].analyze(input_data)

    assert result.status == "partial"
    assert "HTTP_TIMEOUT" in result.errors
    assert any("parcial" in limitation.lower() for limitation in result.limitations)
    assert result.risk_level in {RiskLevel.MEDIUM, RiskLevel.HIGH}


def test_batch_monitor_generates_reports_and_alerts(
    analysis_factory, tmp_path: Path
):
    services = analysis_factory()
    batch_file = tmp_path / "batch.txt"
    batch_file.write_text(
        "banc0lombia-verificacion.xyz\nbancolombia.com.co\n",
        encoding="utf-8",
    )

    batch_result = services["batch_service"].monitor_paths(
        [str(batch_file)],
        output_dir=str(tmp_path / "output"),
        run_id="batch_test",
        enable_content_analysis=False,
    )

    assert len(batch_result["results"]) == 2
    assert batch_result["alerts"]
    assert Path(batch_result["reports"]["tabular_report"]).exists()
    assert Path(batch_result["reports"]["summary_report"]).exists()
