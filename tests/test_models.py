"""Tests for Pydantic models."""

import pytest
from broadcom_support_mcp_server.models import (
    ArticleContent,
    SearchResponse,
    SearchResult,
)


class TestSearchResult:
    def test_basic_creation(self):
        result = SearchResult(title="Test Title", url="https://example.com")
        assert result.title == "Test Title"
        assert result.url == "https://example.com"
        assert result.summary == ''
        assert result.segment == ''

    def test_with_all_fields(self):
        result = SearchResult(
            title="VMware Article",
            url="https://kb.vmware.com/123",
            summary="This is a summary",
            segment="vmware",
        )
        assert result.title == "VMware Article"
        assert result.url == "https://kb.vmware.com/123"
        assert result.summary == "This is a summary"
        assert result.segment == "vmware"

    def test_required_fields_missing(self):
        with pytest.raises(Exception):
            SearchResult(title="Only title")

    def test_url_required(self):
        with pytest.raises(Exception):
            SearchResult(url="https://example.com")


class TestSearchResponse:
    def test_basic_creation(self):
        response = SearchResponse(query="vmware", results=[], total=0)
        assert response.query == "vmware"
        assert response.results == []
        assert response.total == 0

    def test_with_results(self):
        results = [
            SearchResult(title="Article 1", url="https://example.com/1"),
            SearchResult(title="Article 2", url="https://example.com/2"),
        ]
        response = SearchResponse(query="test query", results=results, total=2)
        assert len(response.results) == 2
        assert response.total == 2
        assert response.results[0].title == "Article 1"

    def test_results_are_search_result_instances(self):
        result_data = [{"title": "Test", "url": "https://example.com"}]
        response = SearchResponse(query="test", results=result_data, total=1)
        assert isinstance(response.results[0], SearchResult)


class TestArticleContent:
    def test_basic_creation(self):
        article = ArticleContent(
            title="Test Article",
            url="https://example.com/article",
            content="# Content\n\nSome text here.",
        )
        assert article.title == "Test Article"
        assert article.url == "https://example.com/article"
        assert article.content == "# Content\n\nSome text here."
        assert article.metadata == {}

    def test_with_metadata(self):
        article = ArticleContent(
            title="Article",
            url="https://example.com",
            content="Content",
            metadata={"author": "John", "date": "2024-01-01"},
        )
        assert article.metadata["author"] == "John"
        assert article.metadata["date"] == "2024-01-01"

    def test_metadata_default_factory(self):
        a1 = ArticleContent(title="A1", url="https://a.com", content="c1")
        a2 = ArticleContent(title="A2", url="https://b.com", content="c2")
        # メタデータは独立したインスタンスであることを確認
        a1.metadata["key"] = "value"
        assert "key" not in a2.metadata

    def test_required_fields_missing(self):
        with pytest.raises(Exception):
            ArticleContent(title="Title", url="https://example.com")
