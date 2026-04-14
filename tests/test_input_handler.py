from __future__ import annotations

import pytest

from presentation.input_handler import InputValidationError


def test_prepare_accepts_bare_domain(input_handler):
    prepared = input_handler.prepare("Bancolombia.com.co")

    assert prepared.normalized_domain == "bancolombia.com.co"
    assert prepared.normalized_url == "https://bancolombia.com.co"


def test_prepare_strips_query_and_fragment(input_handler):
    prepared = input_handler.prepare("https://nequi.com.co/login?token=1#frag")

    assert prepared.normalized_url == "https://nequi.com.co/login"
    assert prepared.path == "/login"


def test_prepare_rejects_non_http_scheme(input_handler):
    with pytest.raises(InputValidationError):
        input_handler.prepare("javascript:alert(1)")


def test_prepare_rejects_invalid_domain(input_handler):
    with pytest.raises(InputValidationError):
        input_handler.prepare("dominio-invalido")
