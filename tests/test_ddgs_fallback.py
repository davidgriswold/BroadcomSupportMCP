
"""Regression tests for Broadcom KB search backend fallback.

Mock the DDGS client at the module boundary rather than its internal
methods, keeping tests independent of DDGS proxy implementation details.

Developed with assistance from OpenAI ChatGPT.
"""

import asyncio
from unittest.mock import patch

import pytest

from broadcom_support_mcp_server.client import BroadcomClient


KB_URL = (
    "https://knowledge.broadcom.com/external/article/"
    "446899/official-procedure-for-shutting-down-vks.html"
)


class FakeDDGS:
    """Context-manager-compatible DDGS replacement for isolated tests."""

    calls = []
    responses = {}

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def text(self, query, **kwargs):
        backend = kwargs["backend"]
        self.calls.append(backend)

        response = self.responses[backend]

        if isinstance(response, Exception):
            raise response

        return response


@pytest.fixture
def client():
    return BroadcomClient()


@pytest.fixture
def fake_ddgs():
    """Reset fake provider responses between tests."""
    FakeDDGS.calls = []
    FakeDDGS.responses = {}

    with patch(
        "broadcom_support_mcp_server.client.DDGS",
        FakeDDGS,
    ):
        yield FakeDDGS


def test_backend_failure_triggers_fallback(
    client, fake_ddgs, monkeypatch
):
    """A failed backend must trigger the next configured backend."""
    monkeypatch.setenv("DDGS_BACKENDS", "yahoo,startpage")

    fake_ddgs.responses = {
        "yahoo": RuntimeError("Simulated provider failure"),
        "startpage": [{"href": KB_URL, "title": "VKS Shutdown"}],
    }

    results = asyncio.run(client.search("VKS shutdown"))

    assert fake_ddgs.calls == ["yahoo", "startpage"]
    assert len(results) == 1
    assert results[0]["url"] == KB_URL


def test_irrelevant_results_trigger_fallback(
    client, fake_ddgs, monkeypatch
):
    """Off-site search results must trigger fallback."""
    monkeypatch.setenv("DDGS_BACKENDS", "yahoo,startpage")

    fake_ddgs.responses = {
        "yahoo": [{"href": "https://example.com/unrelated"}],
        "startpage": [{"href": KB_URL, "title": "VKS Shutdown"}],
    }

    results = asyncio.run(client.search("VKS shutdown"))

    assert fake_ddgs.calls == ["yahoo", "startpage"]
    assert len(results) == 1
    assert results[0]["url"] == KB_URL


def test_all_backends_fail(client, fake_ddgs, monkeypatch):
    """Provider outages must raise an explicit error."""
    monkeypatch.setenv("DDGS_BACKENDS", "yahoo,startpage")

    fake_ddgs.responses = {
        "yahoo": RuntimeError("Yahoo unavailable"),
        "startpage": RuntimeError("Startpage unavailable"),
    }

    with pytest.raises(
        RuntimeError,
        match="exhausted all backends",
    ):
        asyncio.run(client.search("VKS shutdown"))

    assert fake_ddgs.calls == ["yahoo", "startpage"]

