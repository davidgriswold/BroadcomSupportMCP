"""Broadcom Support MCP Server - HTTP Client"""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

TIMEOUT = 30.0

# SearchUnify constants
SU_SEARCH_URL = "https://searchunify.broadcom.com/search/searchResultHL"
SU_TOKEN_URL = "https://support.broadcom.com/web/ecx/search/-/searchUnify/suRefreshToken"
SU_UID = "d042dbba-f8c4-11ea-beba-0242ac12000b"
SU_ACCESS_TOKEN = "b72cbbab2728563ec74e93aa3223a7dc"


class BroadcomClient:
    BASE_URL = "https://support.broadcom.com"

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            headers=HEADERS,
            timeout=TIMEOUT,
            follow_redirects=True,
        )
        self._jwt: str = ""

    async def __aenter__(self) -> "BroadcomClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self._client.aclose()

    async def _ensure_jwt(self) -> str:
        """SearchUnify用のJWTトークンを取得する。"""
        if self._jwt:
            return self._jwt
        try:
            resp = await self._client.post(
                SU_TOKEN_URL,
                json={
                    "user_id": "support_portal_su_user",
                    "firstname": "support_portal_su_user",
                    "loggedIn": False,
                },
                headers={"Content-Type": "application/json"},
            )
            resp.raise_for_status()
            self._jwt = resp.text.strip()
        except httpx.HTTPError as exc:
            logger.error("Failed to obtain JWT: %s", exc)
            self._jwt = ""
        return self._jwt

    async def search(
        self,
        query: str,
        segment: str = "all",
        max_results: int = 10,
    ) -> list[dict]:
        """SearchUnify APIでナレッジベース記事を検索する。"""
        jwt = await self._ensure_jwt()

        body: dict[str, Any] = {
            "langAttr": "en",
            "react": 1,
            "searchString": query,
            "from": 0,
            "sortby": "_score",
            "orderBy": "desc",
            "pageNo": 1,
            "aggregations": [{"type": "language", "filter": ["en"]}],
            "uid": SU_UID,
            "resultsPerPage": max_results,
            "language": "en",
            "accessToken": SU_ACCESS_TOKEN,
            "authtoken": jwt,
            "supportCheck": True,
            "versionResults": True,
        }

        try:
            resp = await self._client.post(
                SU_SEARCH_URL,
                json=body,
                headers={"Content-Type": "application/json"},
            )
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPError as exc:
            logger.error("Search request failed: %s", exc)
            return []
        except Exception as exc:
            logger.error("Search parse error: %s", exc)
            return []

        return self._parse_search_response(data, max_results)

    def _parse_search_response(self, data: dict, max_results: int) -> list[dict]:
        """SearchUnify APIレスポンスをパースする。"""
        results: list[dict] = []
        hits = data.get("result", {}).get("hits", [])

        for hit in hits[:max_results]:
            url = hit.get("_id", "")
            highlight = hit.get("highlight", {})

            # タイトルからハイライトマーカーを除去
            raw_title = (highlight.get("title.en") or [""])[0]
            title = (
                raw_title
                .replace("___su-highlight-start___", "")
                .replace("___su-highlight-end___", "")
                .strip()
            )

            # サマリーからハイライトマーカーを除去
            raw_summary = (highlight.get("content.en") or [""])[0]
            summary = (
                raw_summary
                .replace("___su-highlight-start___", "")
                .replace("___su-highlight-end___", "")
                .strip()
            )

            if title or url:
                results.append({
                    "title": title,
                    "url": url,
                    "summary": summary[:300],
                    "segment": "",
                })

        return results

    async def read_article(self, url: str) -> dict:
        """指定URLのナレッジベース記事を取得してパースする。"""
        try:
            response = await self._client.get(url)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error("Article fetch failed with status %s: %s", exc.response.status_code, url)
            return {"title": "", "content": "", "url": url, "metadata": {}, "error": f"HTTP {exc.response.status_code}"}
        except httpx.RequestError as exc:
            logger.error("Article fetch error for %s: %s", url, exc)
            return {"title": "", "content": "", "url": url, "metadata": {}, "error": str(exc)}

        soup = BeautifulSoup(response.text, "html.parser")
        return {
            "title": self._extract_title(soup),
            "content": self._extract_content(soup),
            "url": url,
            "metadata": self._extract_metadata(soup),
        }

    def _extract_title(self, soup: BeautifulSoup) -> str:
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            return og_title["content"].strip()
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)
        title_tag = soup.find("title")
        if title_tag:
            return title_tag.get_text(strip=True)
        return ""

    def _extract_content(self, soup: BeautifulSoup) -> str:
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
            tag.decompose()

        content_selectors = [
            "div[class*='article-body']",
            "div[class*='article-content']",
            "div[class*='kb-article']",
            "div[class*='content-body']",
            "main article", "main",
            "div[role='main']", "div#main-content", "div.content",
        ]
        content_el = None
        for selector in content_selectors:
            content_el = soup.select_one(selector)
            if content_el:
                break
        if content_el is None:
            content_el = soup.find("body") or soup

        return self._html_to_markdown(content_el)

    def _html_to_markdown(self, element: Any) -> str:
        lines: list[str] = []
        for tag in element.find_all(
            ["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "pre", "code", "hr"],
            recursive=True,
        ):
            text = tag.get_text(separator=" ", strip=True)
            if not text:
                continue
            name = tag.name
            if name == "h1":
                lines.append(f"# {text}\n")
            elif name == "h2":
                lines.append(f"## {text}\n")
            elif name == "h3":
                lines.append(f"### {text}\n")
            elif name == "h4":
                lines.append(f"#### {text}\n")
            elif name in ("h5", "h6"):
                lines.append(f"##### {text}\n")
            elif name == "p":
                lines.append(f"{text}\n")
            elif name == "li":
                lines.append(f"- {text}")
            elif name in ("pre", "code"):
                lines.append(f"```\n{text}\n```\n")
            elif name == "hr":
                lines.append("---\n")
        if not lines:
            return element.get_text(separator="\n", strip=True)
        return "\n".join(lines)

    def _extract_metadata(self, soup: BeautifulSoup) -> dict:
        metadata: dict[str, str] = {}
        for meta in soup.find_all("meta"):
            name = meta.get("name") or meta.get("property") or ""
            content = meta.get("content") or ""
            if name and content:
                metadata[name] = content
        return metadata
