"""Tests for formatter functions."""

from broadcom_support_mcp_server.formatters import format_article, format_search_results
from broadcom_support_mcp_server.models import ArticleContent, SearchResponse, SearchResult


class TestFormatSearchResults:
    def test_empty_results(self):
        response = SearchResponse(query="nothing", results=[], total=0)
        output = format_search_results(response)
        assert "nothing" in output
        assert "0 result(s)" in output

    def test_single_result(self):
        results = [
            SearchResult(
                title="VMware KB Article",
                url="https://kb.vmware.com/123",
                summary="This article explains the issue.",
                segment="vmware",
            )
        ]
        response = SearchResponse(query="vmware issue", results=results, total=1)
        output = format_search_results(response)
        assert "vmware issue" in output
        assert "VMware KB Article" in output
        assert "https://kb.vmware.com/123" in output
        assert "This article explains the issue." in output
        assert "vmware" in output
        assert "1 result(s)" in output

    def test_multiple_results(self):
        results = [
            SearchResult(title=f"Article {i}", url=f"https://example.com/{i}")
            for i in range(3)
        ]
        response = SearchResponse(query="test", results=results, total=3)
        output = format_search_results(response)
        assert "3 result(s)" in output
        assert "Article 0" in output
        assert "Article 1" in output
        assert "Article 2" in output

    def test_result_without_summary(self):
        results = [SearchResult(title="No Summary", url="https://example.com")]
        response = SearchResponse(query="test", results=results, total=1)
        output = format_search_results(response)
        assert "No Summary" in output

    def test_result_without_segment(self):
        results = [
            SearchResult(title="No Segment", url="https://example.com", summary="Summary text")
        ]
        response = SearchResponse(query="test", results=results, total=1)
        output = format_search_results(response)
        assert "No Segment" in output
        assert "Summary text" in output

    def test_output_is_markdown(self):
        response = SearchResponse(query="test", results=[], total=0)
        output = format_search_results(response)
        assert output.startswith("#")

    def test_numbered_results(self):
        results = [
            SearchResult(title="First", url="https://example.com/1"),
            SearchResult(title="Second", url="https://example.com/2"),
        ]
        response = SearchResponse(query="test", results=results, total=2)
        output = format_search_results(response)
        assert "1." in output
        assert "2." in output


class TestFormatArticle:
    def test_basic_article(self):
        article = ArticleContent(
            title="How to configure VMware",
            url="https://kb.vmware.com/article",
            content="## Steps\n\n1. Open vSphere\n2. Configure settings",
        )
        output = format_article(article)
        assert "How to configure VMware" in output
        assert "https://kb.vmware.com/article" in output
        assert "Open vSphere" in output

    def test_article_with_metadata(self):
        article = ArticleContent(
            title="Test Article",
            url="https://example.com",
            content="Content here",
            metadata={"author": "Support Team", "version": "1.0"},
        )
        output = format_article(article)
        assert "author" in output
        assert "Support Team" in output
        assert "version" in output
        assert "1.0" in output

    def test_article_without_metadata(self):
        article = ArticleContent(
            title="Simple Article",
            url="https://example.com",
            content="Simple content",
        )
        output = format_article(article)
        assert "Simple Article" in output
        assert "Simple content" in output
        assert "Metadata" not in output

    def test_output_is_markdown(self):
        article = ArticleContent(
            title="Test", url="https://example.com", content="Content"
        )
        output = format_article(article)
        assert output.startswith("# ")

    def test_content_section_present(self):
        article = ArticleContent(
            title="Test", url="https://example.com", content="Article body text"
        )
        output = format_article(article)
        assert "## Content" in output
        assert "Article body text" in output
