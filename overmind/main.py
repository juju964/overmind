from __future__ import annotations

import argparse
import asyncio
from pprint import pprint

from .crawler import AsyncCrawler
from .indexer import Document, InvertedIndex
from .semantic import SemanticRanker
from .simulation import pagerank


def build_from_seeds(seeds: list[str], max_pages: int = 20) -> tuple[InvertedIndex, dict[str, float]]:
    crawler = AsyncCrawler(workers=4, max_pages=max_pages)
    pages = asyncio.run(crawler.crawl(seeds))

    index = InvertedIndex()
    for i, page in enumerate(pages):
        index.add_document(Document(doc_id=f"doc-{i}", title=page.title, url=page.url, text=page.text))

    graph = {page.url: [link for link in page.links if link in {p.url for p in pages}] for page in pages}
    ranks = pagerank(graph)
    return index, ranks


def run_query(index: InvertedIndex, query: str) -> None:
    ranker = SemanticRanker(index)
    results = ranker.search(query, top_k=5)
    pprint([{"title": r.title, "url": r.url, "score": round(r.score, 4)} for r in results])


def main() -> None:
    parser = argparse.ArgumentParser(description="Overmind MVP: crawler + indexing + semantic search")
    parser.add_argument("query", help="Natural language query")
    parser.add_argument("--seed", action="append", required=True, help="Seed URL(s) to crawl")
    parser.add_argument("--max-pages", type=int, default=20)
    args = parser.parse_args()

    index, ranks = build_from_seeds(args.seed, args.max_pages)
    print(f"Indexed {len(index.documents)} documents")
    print("Top PageRank:")
    pprint(sorted(ranks.items(), key=lambda item: item[1], reverse=True)[:5])
    print("Search results:")
    run_query(index, args.query)


if __name__ == "__main__":
    main()
