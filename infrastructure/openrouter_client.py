from __future__ import annotations

import json
import socket
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class OpenRouterClientError(RuntimeError):
    pass


class OpenRouterClient:
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://openrouter.ai/api/v1/chat/completions",
        timeout_seconds: float = 20.0,
        app_referer: str = "",
        app_title: str = "PhishingCol",
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url
        self._timeout_seconds = timeout_seconds
        self._app_referer = app_referer
        self._app_title = app_title

    def create_chat_completion(self, payload: dict[str, object]) -> dict[str, object]:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self._app_referer:
            headers["HTTP-Referer"] = self._app_referer
        if self._app_title:
            headers["X-OpenRouter-Title"] = self._app_title

        request = Request(
            self._base_url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        try:
            with urlopen(request, timeout=self._timeout_seconds) as response:  # nosec B310
                body = response.read().decode("utf-8", errors="ignore")
                return json.loads(body)
        except HTTPError as error:
            detail = error.read().decode("utf-8", errors="ignore")
            raise OpenRouterClientError(
                f"OpenRouter devolvio HTTP {error.code}: {detail}"
            ) from error
        except (URLError, TimeoutError, socket.timeout) as error:
            raise OpenRouterClientError(
                "No fue posible conectar con OpenRouter o la solicitud excedio el timeout."
            ) from error
        except json.JSONDecodeError as error:
            raise OpenRouterClientError(
                "OpenRouter respondio con un cuerpo no valido en JSON."
            ) from error
