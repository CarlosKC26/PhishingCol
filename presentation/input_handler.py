from __future__ import annotations

import re
from urllib.parse import urlsplit, urlunsplit

from domain.models import DomainInput


HOST_PATTERN = re.compile(
    r"^(?=.{1,253}$)(?!-)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$"
)


class InputValidationError(ValueError):
    """Raised when the provided URL or domain is not processable."""


class InputHandler:
    def __init__(
        self,
        analysis_timeout_seconds: float = 10.0,
        content_timeout_seconds: float = 2.0,
    ) -> None:
        self._analysis_timeout_seconds = analysis_timeout_seconds
        self._content_timeout_seconds = content_timeout_seconds

    def prepare(
        self,
        raw_value: str,
        source: str = "manual",
        enable_content_analysis: bool = True,
        analysis_timeout_seconds: float | None = None,
        content_timeout_seconds: float | None = None,
        run_id: str = "manual",
    ) -> DomainInput:
        sanitized = self._sanitize(raw_value)
        parsed = self._parse_url_or_domain(sanitized)
        domain = (parsed.hostname or "").strip(".").lower()

        if not self._is_valid_domain(domain):
            raise InputValidationError(
                "La entrada no corresponde a un dominio o URL válido."
            )

        normalized_path = parsed.path or ""
        normalized_url = urlunsplit(
            (parsed.scheme.lower(), domain, normalized_path, "", "")
        )

        return DomainInput(
            original_value=sanitized,
            normalized_url=normalized_url,
            normalized_domain=domain,
            scheme=parsed.scheme.lower(),
            path=normalized_path,
            source=source,
            enable_content_analysis=enable_content_analysis,
            analysis_timeout_seconds=analysis_timeout_seconds
            or self._analysis_timeout_seconds,
            content_timeout_seconds=content_timeout_seconds
            or self._content_timeout_seconds,
            run_id=run_id,
        )

    @staticmethod
    def _sanitize(raw_value: str) -> str:
        sanitized = raw_value.strip()
        if not sanitized:
            raise InputValidationError("Debe ingresar una URL o dominio.")
        if len(sanitized) > 2048:
            raise InputValidationError("La entrada supera la longitud permitida.")
        return sanitized

    def _parse_url_or_domain(self, sanitized: str):
        candidate = sanitized
        if "://" not in candidate:
            candidate = f"https://{candidate}"

        parsed = urlsplit(candidate)
        if parsed.scheme.lower() not in {"http", "https"}:
            raise InputValidationError("Solo se permiten URLs HTTP/HTTPS o dominios.")
        return parsed

    @staticmethod
    def _is_valid_domain(domain: str) -> bool:
        return bool(HOST_PATTERN.fullmatch(domain))
