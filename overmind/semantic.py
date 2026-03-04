from __future__ import annotations

import math
from collections import defaultdict

from .indexer import InvertedIndex, SearchResult
from .text import tokenize


class SemanticRanker:
    """Simple co-occurrence embedding (Word2Vec-like approximation)."""

    def __init__(self, index: InvertedIndex, window: int = 2) -> None:
        self.index = index
        self.window = window
        self.vectors: dict[str, dict[str, float]] = defaultdict(dict)
        self._trained = False

    def train(self) -> None:
        counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for doc in self.index.documents.values():
            tokens = tokenize(doc.text)
            for i, token in enumerate(tokens):
                for j in range(max(0, i - self.window), min(len(tokens), i + self.window + 1)):
                    if i == j:
                        continue
                    context = tokens[j]
                    counts[token][context] += 1

        for word, ctx_counts in counts.items():
            norm = math.sqrt(sum(v * v for v in ctx_counts.values())) or 1.0
            self.vectors[word] = {ctx: val / norm for ctx, val in ctx_counts.items()}
        self._trained = True

    def _cosine_sparse(self, left: dict[str, float], right: dict[str, float]) -> float:
        if not left or not right:
            return 0.0
        common = set(left) & set(right)
        dot = sum(left[k] * right[k] for k in common)
        left_norm = math.sqrt(sum(v * v for v in left.values())) or 1.0
        right_norm = math.sqrt(sum(v * v for v in right.values())) or 1.0
        return dot / (left_norm * right_norm)

    def _text_vector(self, text: str) -> dict[str, float]:
        tokens = tokenize(text)
        if not tokens:
            return {}
        vector: dict[str, float] = defaultdict(float)
        for token in tokens:
            for dim, val in self.vectors.get(token, {}).items():
                vector[dim] += val
        norm = math.sqrt(sum(v * v for v in vector.values())) or 1.0
        return {k: v / norm for k, v in vector.items()}

    def search(self, query: str, top_k: int = 10, alpha: float = 0.6) -> list[SearchResult]:
        if not self._trained:
            self.train()
        lexical = self.index.search(query, top_k=max(top_k * 3, 10))
        qvec = self._text_vector(query)

        fused: list[SearchResult] = []
        for item in lexical:
            doc = self.index.documents[item.doc_id]
            dvec = self._text_vector(doc.text)
            semantic = self._cosine_sparse(qvec, dvec)
            score = alpha * item.score + (1 - alpha) * semantic
            fused.append(SearchResult(doc_id=item.doc_id, score=score, title=item.title, url=item.url))

        fused.sort(key=lambda r: r.score, reverse=True)
        return fused[:top_k]
