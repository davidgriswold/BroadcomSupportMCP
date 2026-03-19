"""Pydantic models for Broadcom Support MCP Server."""

from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    title: str
    url: str
    summary: str = ''
    segment: str = ''


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
    total: int


class ArticleContent(BaseModel):
    title: str
    url: str
    content: str  # markdown形式
    metadata: dict = Field(default_factory=dict)
