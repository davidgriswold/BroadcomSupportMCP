"""Broadcom Support MCP Server."""

import argparse

from fastmcp import FastMCP
from .client import BroadcomClient

mcp = FastMCP(
    "broadcom-support-mcp-server",
    instructions=(
        "This server provides tools to search and read Broadcom Support "
        "knowledge base articles."
    ),
)

_client = BroadcomClient()


@mcp.tool(
    name="search_documentation",
    description=(
        "Search the Broadcom Support knowledge base for articles matching the query. "
        "Returns a list of relevant articles with titles, URLs, and snippets."
    ),
)
@mcp.tool(
    name="search_documentation",
    description=(
        "Search the Broadcom Support knowledge base for articles matching the query. "
        "Returns a list of relevant articles with titles, URLs, and snippets."
    ),
)
@mcp.tool(
    name="search_documentation",
    description=(
        "Search the Broadcom Support knowledge base for articles matching the query. "
        "Returns a list of relevant articles with titles, URLs, and snippets."
    ),
)
async def search_documentation(query: str, segment: str = "all") -> str:
    """Search Broadcom Support knowledge base.

    Args:
        query: Search query string.
        segment: Product segment to filter results (default: 'all').

    Returns:
        Formatted string containing search results.
    """
    import json
    results = await _client.search(query=query, segment=segment)
    return json.dumps({"query": query, "segment": segment, "results": results}, ensure_ascii=False, indent=2)


@mcp.tool(
    name="read_documentation",
    description=(
        "Retrieve the full content of a Broadcom Support article at the given URL. "
        "Returns the article title, body text, and metadata."
    ),
)
@mcp.tool(
    name="read_documentation",
    description=(
        "Retrieve the full content of a Broadcom Support article at the given URL. "
        "Returns the article title, body text, and metadata."
    ),
)
async def read_documentation(url: str) -> dict:
    """Fetch article content from a URL.

    Args:
        url: URL of the Broadcom Support article to retrieve.

    Returns:
        dict containing article title, content, and metadata.
    """
    return await _client.read_article(url=url)

def main() -> None:
    """Start the MCP server using the selected transport.

    Defaults to stdio for backward compatibility. HTTP mode uses
    Streamable HTTP and binds to localhost unless explicitly configured.
    """
    parser = argparse.ArgumentParser(
        description="Broadcom Support Knowledge Base MCP Server"
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="MCP transport (default: stdio)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="HTTP bind address (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="HTTP listening port (default: 8000)",
    )

    args = parser.parse_args()

    if args.transport == "http":
        if not 1 <= args.port <= 65535:
            parser.error("--port must be between 1 and 65535")

        mcp.run(
            transport="http",
            host=args.host,
            port=args.port,
        )
    else:
        mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
