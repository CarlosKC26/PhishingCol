from __future__ import annotations

import socket
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from domain.models import StaticContentSnapshot


class _StaticHTMLParser(HTMLParser):
    def __init__(self, max_chars: int = 800) -> None:
        super().__init__()
        self._max_chars = max_chars
        self._in_title = False
        self._in_script_or_style = False
        self.title_parts: list[str] = []
        self.text_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:  # type: ignore[override]
        if tag == "title":
            self._in_title = True
        if tag in {"script", "style"}:
            self._in_script_or_style = True

    def handle_endtag(self, tag: str) -> None:  # type: ignore[override]
        if tag == "title":
            self._in_title = False
        if tag in {"script", "style"}:
            self._in_script_or_style = False

    def handle_data(self, data: str) -> None:  # type: ignore[override]
        clean = " ".join(data.split())
        if not clean or self._in_script_or_style:
            return

        if self._in_title:
            self.title_parts.append(clean)
            return

        if len(" ".join(self.text_parts)) < self._max_chars:
            self.text_parts.append(clean)

    @property
    def title(self) -> str:
        return " ".join(self.title_parts).strip()

    @property
    def text_excerpt(self) -> str:
        return " ".join(self.text_parts).strip()[: self._max_chars]


class StaticContentFetcher:
    def fetch(self, url: str, timeout_seconds: float) -> StaticContentSnapshot:
        request = Request(
            url,
            headers={
                "User-Agent": "PhishingCol/1.0",
                "Accept": "text/html,application/xhtml+xml",
            },
        )
        try:
            with urlopen(request, timeout=timeout_seconds) as response:
                raw_body = response.read(65536)
                charset = response.headers.get_content_charset() or "utf-8"
                body = raw_body.decode(charset, errors="ignore")
                parser = _StaticHTMLParser()
                parser.feed(body)
                final_url = response.geturl()
                return StaticContentSnapshot(
                    requested_url=url,
                    final_url=final_url,
                    status_code=getattr(response, "status", None),
                    title=parser.title,
                    text_excerpt=parser.text_excerpt,
                    redirected=final_url != url,
                )
        except HTTPError as error:
            return StaticContentSnapshot(
                requested_url=url,
                status_code=error.code,
                error_code="HTTP_ERROR",
                limitation=(
                    "El contenido estático no estuvo disponible; se devolvió un análisis parcial."
                ),
            )
        except (URLError, TimeoutError, socket.timeout):
            return StaticContentSnapshot(
                requested_url=url,
                error_code="HTTP_TIMEOUT",
                limitation=(
                    "El análisis de contenido excedió el tiempo o no fue accesible; "
                    "se devolvió un análisis parcial."
                ),
            )
        except Exception:
            return StaticContentSnapshot(
                requested_url=url,
                error_code="CONTENT_ANALYSIS_ERROR",
                limitation=(
                    "No fue posible completar el análisis de contenido estático; "
                    "se mantuvo la evaluación estructural."
                ),
            )
