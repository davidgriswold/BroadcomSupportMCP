"""Broadcom Support MCP Server - HTTP Client."""

from __future__ import annotations

import asyncio
import logging
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from ddgs import DDGS

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

    async def search(
        self,
        query: str,
        segment: str = "all",
        max_results: int = 5,
    ) -> list[dict]:
        """Search Broadcom KB articles using configurable DDGS backends.

        Backends are attempted in priority order. A backend is considered
        successful only when it returns valid Broadcom KB article URLs.

        DDGS is synchronous, so each search runs outside the asyncio event
        loop. Search failures are logged without treating them as evidence
        that no matching documentation exists.

        The segment parameter is retained for MCP compatibility.
        """
        import os
        import time

        search_query = (
            f"site:knowledge.broadcom.com/external/article/ {query}"
        )

        backends = [
            name.strip().lower()
            for name in os.getenv(
                "DDGS_BACKENDS",
                "yahoo,startpage,brave,mojeek",
            ).split(",")
            if name.strip()
        ]

        if not backends:
            raise ValueError("DDGS_BACKENDS contains no search backends")

        # Provider identifiers observed in DDGS 9.16.1.
        providers = {
            "yahoo": "bing",
            "duckduckgo": "bing",
            "startpage": "google",
            "brave": "brave",
            "mojeek": "mojeek",
        }

        failures = []

        for backend in backends:
            started = time.monotonic()

            def run_search() -> list[dict]:
                with DDGS(timeout=10) as ddgs:
                    return list(ddgs.text(
                        search_query,
                        backend=backend,
                        max_results=max_results,
                    ))

            try:
                hits = await asyncio.to_thread(run_search)
            except Exception as exc:
                elapsed = time.monotonic() - started
                failures.append((backend, str(exc)))

                logger.warning(
                    "DDGS backend=%s provider=%s "
                    "duration=%.2fs status=error error=%r",
                    backend,
                    providers.get(backend, "unknown"),
                    elapsed,
                    exc,
                )
                continue

            results = []
            for hit in hits:
                url = hit.get("href", "")
                parsed = urlparse(url)

                # Accept only official HTTPS Broadcom KB articles.
                if (
                    parsed.scheme != "https"
                    or parsed.hostname != "knowledge.broadcom.com"
                    or not parsed.path.startswith("/external/article/")
                ):
                    continue

                results.append({
                    "title": hit.get("title", ""),
                    "url": url,
                    "summary": (hit.get("body") or "")[:300],
                    "segment": "",
                })

            elapsed = time.monotonic() - started

            logger.warning(
                "DDGS backend=%s provider=%s "
                "duration=%.2fs raw=%d valid=%d",
                backend,
                providers.get(backend, "unknown"),
                elapsed,
                len(hits),
                len(results),
            )

            if results:
                return results

        # Preserve the distinction between an unsuccessful search
        # and a confirmed absence of matching articles.
        if failures:
            raise RuntimeError(
                "Broadcom KB search exhausted all backends; "
                f"{len(failures)} backend(s) reported errors"
            )

        return []

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

        article = {
            "title": self._extract_title(soup),
            "content": self._extract_content(soup),
            "url": url,
            "metadata": self._extract_metadata(soup),
        }

        logger.warning(
            "Broadcom KB retrieved url=%s status=%d content_chars=%d",
            url,
            response.status_code,
            len(article["content"]),
        )

        return article

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

