from __future__ import annotations

import json

from domain.models import AISummaryResult, AnalysisResult
from infrastructure.openrouter_client import OpenRouterClient, OpenRouterClientError


class OpenRouterSummaryGenerator:
    DISCLAIMER = (
        "Este resumen fue generado por inteligencia artificial a partir de los "
        "resultados deterministas del sistema. No modifica el score ni el nivel "
        "de riesgo calculados por PhishingCol."
    )

    def __init__(
        self,
        client: OpenRouterClient,
        model: str = "",
    ) -> None:
        self._client = client
        self._model = model

    def generate(self, result: AnalysisResult) -> AISummaryResult:
        payload = self._build_payload(result)
        response = self._client.create_chat_completion(payload)
        content = self._extract_content(response)
        parsed = self._parse_json_object(content)

        narrative_summary = self._clean_text(parsed.get("narrative_summary", ""))
        suggested_steps = self._clean_steps(parsed.get("suggested_steps", []))
        if not narrative_summary or not suggested_steps:
            raise OpenRouterClientError(
                "La respuesta de OpenRouter no incluyo el resumen esperado."
            )

        return AISummaryResult(
            narrative_summary=narrative_summary,
            suggested_steps=tuple(suggested_steps),
            disclaimer=self.DISCLAIMER,
            provider="OpenRouter",
            model=self._model or "default",
        )

    def _build_payload(self, result: AnalysisResult) -> dict[str, object]:
        analysis_payload = {
            "input_value": result.input_value,
            "normalized_domain": result.normalized_domain,
            "risk_level": result.risk_level.value,
            "score": result.score,
            "status": result.status,
            "matched_brands": list(result.matched_brands),
            "triggered_rules": [
                {
                    "rule_id": rule.rule_id,
                    "name": rule.name,
                    "weight": rule.weight,
                    "evidence": list(rule.evidence),
                }
                for rule in result.score_breakdown.matched_rules
            ],
            "evidence": list(result.explanation.evidence),
            "limitations": list(result.explanation.limitations),
            "summary": result.explanation.summary,
        }
        prompt = (
            "Convierte el siguiente analisis de phishing en un resumen para una "
            "persona no tecnica. No inventes nueva evidencia, no cambies el score, "
            "no cambies el nivel de riesgo y no afirmes cosas que no esten en el "
            "analisis. Responde solo con un objeto JSON con esta forma exacta: "
            '{"narrative_summary":"texto","suggested_steps":["paso 1","paso 2","paso 3"]}. '
            "El resumen debe tener entre 2 y 4 frases. Los pasos sugeridos deben "
            "ser claros, accionables y maximo 4.\n\nAnalisis:\n"
            + json.dumps(analysis_payload, ensure_ascii=False, indent=2)
        )
        payload: dict[str, object] = {
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Eres un asistente de ciberseguridad que reescribe analisis "
                        "deterministas en lenguaje humano sin alterar sus resultados."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 500,
        }
        if self._model:
            payload["model"] = self._model
        return payload

    @staticmethod
    def _extract_content(response: dict[str, object]) -> str:
        choices = response.get("choices")
        if not isinstance(choices, list) or not choices:
            raise OpenRouterClientError("OpenRouter no devolvio opciones de respuesta.")

        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise OpenRouterClientError("La respuesta de OpenRouter tuvo un formato inesperado.")

        message = first_choice.get("message")
        if not isinstance(message, dict):
            raise OpenRouterClientError("OpenRouter no devolvio un mensaje valido.")

        content = message.get("content", "")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            text_parts: list[str] = []
            for item in content:
                if isinstance(item, dict):
                    text = item.get("text")
                    if isinstance(text, str):
                        text_parts.append(text)
            return "\n".join(text_parts)
        raise OpenRouterClientError("No fue posible leer el contenido de OpenRouter.")

    @staticmethod
    def _parse_json_object(content: str) -> dict[str, object]:
        cleaned = content.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.startswith("json"):
                cleaned = cleaned[4:].strip()

        start_index = cleaned.find("{")
        end_index = cleaned.rfind("}")
        if start_index == -1 or end_index == -1 or end_index <= start_index:
            raise OpenRouterClientError("La respuesta de OpenRouter no contiene JSON valido.")

        try:
            payload = json.loads(cleaned[start_index : end_index + 1])
        except json.JSONDecodeError as error:
            raise OpenRouterClientError(
                "La respuesta de OpenRouter no pudo parsearse como JSON."
            ) from error

        if not isinstance(payload, dict):
            raise OpenRouterClientError("La respuesta de OpenRouter no fue un objeto JSON.")
        return payload

    @staticmethod
    def _clean_text(value: object) -> str:
        if not isinstance(value, str):
            return ""
        return " ".join(value.split())

    @staticmethod
    def _clean_steps(value: object) -> list[str]:
        if not isinstance(value, list):
            return []
        steps = []
        for item in value:
            if not isinstance(item, str):
                continue
            cleaned = " ".join(item.split())
            if cleaned:
                steps.append(cleaned)
        return steps[:4]
