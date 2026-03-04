from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from .text import clean_html, detect_language

_LINK_RE = re.compile(r'href=["\'](.*?)["\']', re.IGNORECASE)


@dataclass
class CrawledPage:
    url: str
    title: str
    text: str
    language: str
    links: list[str]


class AsyncCrawler:
    def __init__(self, workers: int = 4, max_pages: int = 100, allowed_domains: set[str] | None = None) -> None:
        self.workers = workers
        self.max_pages = max_pages
        self.allowed_domains = allowed_domains
        self._visited: set[str] = set()
        self._queue: asyncio.Queue[str] = asyncio.Queue()
        self._results: list[CrawledPage] = []

    async def _fetch(self, url: str) -> str:
        loop = asyncio.get_running_loop()

        def _blocking_fetch() -> str:
            req = Request(url, headers={"User-Agent": "OvermindBot/0.1"})
            with urlopen(req, timeout=8) as response:
                if "text/html" not in response.headers.get("Content-Type", ""):
                    return ""
                return response.read().decode("utf-8", errors="ignore")

        return await loop.run_in_executor(None, _blocking_fetch)

    def _extract_links(self, base_url: str, html: str) -> list[str]:
        links = []
        for href in _LINK_RE.findall(html):
            absolute = urljoin(base_url, href)
            parsed = urlparse(absolute)
            if parsed.scheme in {"http", "https"}:
                links.append(f"{parsed.scheme}://{parsed.netloc}{parsed.path}")
        return links

    async def _worker(self) -> None:
        while len(self._results) < self.max_pages:
            try:
                url = await asyncio.wait_for(self._queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                return
            if url in self._visited:
                self._queue.task_done()
                continue
            self._visited.add(url)

            if self.allowed_domains and urlparse(url).netloc not in self.allowed_domains:
                self._queue.task_done()
                continue

            try:
                html = await self._fetch(url)
            except Exception:
                self._queue.task_done()
                continue

            if not html:
                self._queue.task_done()
                continue

            text = clean_html(html)
            title_match = re.search(r"<title>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
            title = clean_html(title_match.group(1)) if title_match else url
            links = self._extract_links(url, html)
            self._results.append(
                CrawledPage(url=url, title=title, text=text, language=detect_language(text), links=links)
            )

            for link in links:
                if link not in self._visited and self._queue.qsize() < self.max_pages * 3:
                    await self._queue.put(link)

            self._queue.task_done()

    async def crawl(self, seeds: list[str]) -> list[CrawledPage]:
        for seed in seeds:
            await self._queue.put(seed)
        tasks = [asyncio.create_task(self._worker()) for _ in range(self.workers)]
        await asyncio.gather(*tasks)
        return self._results
