"""Regression tests for MCP tool registration."""

import ast
import asyncio
from pathlib import Path

from broadcom_support_mcp_server.server import mcp


def test_each_function_has_one_mcp_tool_decorator():
    """Prevent duplicate @mcp.tool decorators on a single function."""
    server_path = (
        Path(__file__).resolve().parents[1]
        / "broadcom_support_mcp_server"
        / "server.py"
    )
    tree = ast.parse(server_path.read_text(encoding="utf-8"))

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        decorators = [
            decorator
            for decorator in node.decorator_list
            if isinstance(decorator, ast.Call)
            and isinstance(decorator.func, ast.Attribute)
            and isinstance(decorator.func.value, ast.Name)
            and decorator.func.value.id == "mcp"
            and decorator.func.attr == "tool"
        ]

        assert len(decorators) <= 1, (
            f"{node.name} has {len(decorators)} @mcp.tool decorators"
        )


def test_expected_tools_are_registered():
    """Verify the server exposes its two documented MCP tools."""
    async def get_tool_names():
        tools = await mcp.list_tools()
        return [tool.name for tool in tools]

    names = asyncio.run(get_tool_names())

    assert sorted(names) == [
        "read_documentation",
        "search_documentation",
    ]
