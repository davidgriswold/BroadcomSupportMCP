"""Regression tests for MCP server command-line configuration.

Mock server startup so tests verify transport selection without opening
network sockets or starting a long-running MCP process.
"""

import sys
from unittest.mock import patch

import pytest

from broadcom_support_mcp_server import server


def test_default_transport_uses_stdio(monkeypatch):
    """Preserve stdio as the default for existing MCP clients."""
    monkeypatch.setattr(sys, "argv", ["broadcom-support-mcp-server"])

    with patch.object(server.mcp, "run") as run:
        server.main()

    run.assert_called_once_with(transport="stdio")


def test_http_transport_uses_safe_defaults(monkeypatch):
    """HTTP must bind to localhost unless explicitly configured."""
    monkeypatch.setattr(
        sys, "argv",
        ["broadcom-support-mcp-server", "--transport", "http"],
    )

    with patch.object(server.mcp, "run") as run:
        server.main()

    run.assert_called_once_with(
        transport="http", host="127.0.0.1", port=8000
    )


def test_http_transport_accepts_custom_host_and_port(monkeypatch):
    """Allow an operator to select an HTTP listening interface and port."""
    monkeypatch.setattr(
        sys, "argv",
        [
            "broadcom-support-mcp-server",
            "--transport", "http",
            "--host", "0.0.0.0",
            "--port", "8080",
        ],
    )

    with patch.object(server.mcp, "run") as run:
        server.main()

    run.assert_called_once_with(
        transport="http", host="0.0.0.0", port=8080
    )


@pytest.mark.parametrize("port", ["0", "65536", "-1", "abc"])
def test_http_rejects_invalid_ports(monkeypatch, port):
    """Reject ports outside the TCP range and nonnumeric values."""
    monkeypatch.setattr(
        sys, "argv",
        [
            "broadcom-support-mcp-server",
            "--transport", "http",
            "--port", port,
        ],
    )

    with patch.object(server.mcp, "run") as run:
        with pytest.raises(SystemExit) as exc:
            server.main()

    assert exc.value.code == 2
    run.assert_not_called()


def test_invalid_transport_is_rejected(monkeypatch):
    """Reject unsupported transports rather than silently falling back."""
    monkeypatch.setattr(
        sys, "argv",
        ["broadcom-support-mcp-server", "--transport", "sse"],
    )

    with patch.object(server.mcp, "run") as run:
        with pytest.raises(SystemExit) as exc:
            server.main()

    assert exc.value.code == 2
    run.assert_not_called()
