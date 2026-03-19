from broadcom_support_mcp_server.models import ArticleContent, SearchResponse


def format_search_results(response: SearchResponse) -> str:
    """検索結果をmarkdown形式の文字列にフォーマット"""
    lines = [
        f"# Search Results for: {response.query}",
        f"",
        f"Found {response.total} result(s)",
        f"",
    ]

    for i, result in enumerate(response.results, 1):
        lines.append(f"## {i}. {result.title}")
        lines.append(f"")
        lines.append(f"**URL:** {result.url}")
        if result.segment:
            lines.append(f"**Segment:** {result.segment}")
        if result.summary:
            lines.append(f"")
            lines.append(result.summary)
        lines.append(f"")

    return "\n".join(lines)


def format_article(article: ArticleContent) -> str:
    """記事内容をmarkdown形式にフォーマット"""
    lines = [
        f"# {article.title}",
        f"",
        f"**URL:** {article.url}",
    ]

    if article.metadata:
        lines.append(f"")
        lines.append(f"## Metadata")
        lines.append(f"")
        for key, value in article.metadata.items():
            lines.append(f"- **{key}:** {value}")

    lines.append(f"")
    lines.append(f"## Content")
    lines.append(f"")
    lines.append(article.content)

    return "\n".join(lines)
