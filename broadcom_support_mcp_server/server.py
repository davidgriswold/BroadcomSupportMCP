"""Broadcom Support MCP Server."""

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
async def read_documentation(url: str) -> dict:
    """Fetch article content from a URL.

    Args:
        url: URL of the Broadcom Support article to retrieve.

    Returns:
        dict containing article title, content, and metadata.
    """
    return await _client.read_article(url=url)


def main() -> None:
    """Entry point for the Broadcom Support MCP Server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
