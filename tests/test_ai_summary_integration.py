from __future__ import annotations

import json
from pathlib import Path

from application.ai_summary_service import AISummaryService
from domain.models import RiskLevel
from infrastructure.logging_monitoring import LoggingMonitoring
from infrastructure.openrouter_client import OpenRouterClient
from infrastructure.openrouter_summary_generator import OpenRouterSummaryGenerator


class FakeOpenRouterClient:
    def __init__(self, content: str) -> None:
        self._content = content

    def create_chat_completion(self, payload: dict[str, object]) -> dict[str, object]:
        return {
            "choices": [
                {
                    "message": {
                        "content": self._content,
                    }
                }
            ]
        }


class FailingGenerator:
    def generate(self, result):  # pragma: no cover - behavior tested via service
        raise RuntimeError("boom")


class _FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = payload

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_openrouter_summary_generator_returns_structured_summary(
    analysis_factory, input_handler
):
    services = analysis_factory()
    input_data = input_handler.prepare("https://banc0lombia-verificacion.xyz/login")
    result = services["analysis_service"].analyze(input_data)

    generator = OpenRouterSummaryGenerator(
        client=FakeOpenRouterClient(
            '{"narrative_summary":"El dominio tiene senales claras de suplantacion y alto riesgo.","suggested_steps":["No ingreses credenciales.","Verifica el dominio oficial.","Reporta el hallazgo."]}'
        ),
        model="demo-model",
    )

    summary = generator.generate(result)

    assert summary.provider == "OpenRouter"
    assert summary.model == "demo-model"
    assert "No modifica el score" in summary.disclaimer
    assert len(summary.suggested_steps) == 3


def test_openrouter_summary_generator_accepts_markdown_wrapped_json(
    analysis_factory, input_handler
):
    services = analysis_factory()
    input_data = input_handler.prepare("https://davivienda-validacion-pago-click.top/login")
    result = services["analysis_service"].analyze(input_data)

    generator = OpenRouterSummaryGenerator(
        client=FakeOpenRouterClient(
            '```json\n{"narrative_summary":"El dominio combina senales de marca y validacion sospechosa.","suggested_steps":["Evita iniciar sesion.","Consulta canales oficiales.","Monitorea movimientos recientes."]}\n```'
        ),
        model="demo-model",
    )

    summary = generator.generate(result)

    assert "marca" in summary.narrative_summary.lower()
    assert summary.suggested_steps[0] == "Evita iniciar sesion."


def test_ai_summary_service_returns_none_when_generator_fails(
    analysis_factory, input_handler, tmp_path: Path
):
    services = analysis_factory()
    input_data = input_handler.prepare("https://nequi-verificacion.xyz/login")
    result = services["analysis_service"].analyze(input_data)
    logger = LoggingMonitoring(logger_name=f"ai_summary_tests_{tmp_path.name}")
    service = AISummaryService(FailingGenerator(), logger)

    summary = service.summarize(result)

    assert summary is None


def test_openrouter_client_parses_non_streaming_response(monkeypatch):
    client = OpenRouterClient(
        api_key="demo-key",
        base_url="https://openrouter.ai/api/v1/chat/completions",
        timeout_seconds=5,
        app_referer="http://localhost",
        app_title="PhishingCol",
    )

    def fake_urlopen(request, timeout):  # noqa: ANN001
        return _FakeResponse({"choices": [{"message": {"content": "ok"}}]})

    monkeypatch.setattr("infrastructure.openrouter_client.urlopen", fake_urlopen)

    payload = client.create_chat_completion(
        {"messages": [{"role": "user", "content": "hola"}]}
    )

    assert payload["choices"][0]["message"]["content"] == "ok"


def test_ai_summary_flow_does_not_modify_risk_level(analysis_factory, input_handler):
    services = analysis_factory()
    input_data = input_handler.prepare("https://banc0lombia-verificacion.xyz/login")
    result = services["analysis_service"].analyze(input_data)

    generator = OpenRouterSummaryGenerator(
        client=FakeOpenRouterClient(
            '{"narrative_summary":"Es un hallazgo de riesgo alto.","suggested_steps":["No interactues con el sitio.","Consulta el canal oficial.","Cambia tus credenciales si ya ingresaste datos."]}'
        ),
        model="demo-model",
    )
    summary = generator.generate(result)

    assert result.risk_level == RiskLevel.HIGH
    assert "riesgo alto" in summary.narrative_summary.lower()
