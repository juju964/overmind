from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable

from .text import term_freq, tokenize


@dataclass(frozen=True)
class Document:
    doc_id: str
    title: str
    url: str
    text: str


@dataclass(frozen=True)
class SearchResult:
    doc_id: str
    score: float
    title: str
    url: str


class InvertedIndex:
    def __init__(self) -> None:
        self._docs: dict[str, Document] = {}
        self._postings: dict[str, dict[str, int]] = defaultdict(dict)
        self._doc_norms: dict[str, float] = {}

    @property
    def documents(self) -> dict[str, Document]:
        return self._docs

    def add_document(self, doc: Document) -> None:
        tokens = tokenize(doc.text)
        tf = term_freq(tokens)
        self._docs[doc.doc_id] = doc
        for token, freq in tf.items():
            self._postings[token][doc.doc_id] = freq
        self._compute_doc_norm(doc.doc_id, tf)

    def _idf(self, token: str) -> float:
        n_docs = max(len(self._docs), 1)
        df = len(self._postings.get(token, {}))
        return math.log((1 + n_docs) / (1 + df)) + 1.0

    def _compute_doc_norm(self, doc_id: str, tf_map: dict[str, int]) -> None:
        squared_sum = 0.0
        for token, count in tf_map.items():
            weight = (1 + math.log(count)) * self._idf(token)
            squared_sum += weight * weight
        self._doc_norms[doc_id] = math.sqrt(squared_sum) if squared_sum else 1.0

    def search(self, query: str, top_k: int = 10) -> list[SearchResult]:
        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        query_tf = term_freq(query_tokens)
        query_vec: dict[str, float] = {}
        query_norm_sq = 0.0
        for token, count in query_tf.items():
            q_weight = (1 + math.log(count)) * self._idf(token)
            query_vec[token] = q_weight
            query_norm_sq += q_weight * q_weight
        query_norm = math.sqrt(query_norm_sq) if query_norm_sq else 1.0

        scores: dict[str, float] = defaultdict(float)
        for token, q_weight in query_vec.items():
            for doc_id, tf in self._postings.get(token, {}).items():
                d_weight = (1 + math.log(tf)) * self._idf(token)
                scores[doc_id] += q_weight * d_weight

        ranked = []
        for doc_id, dot in scores.items():
            norm = self._doc_norms.get(doc_id, 1.0)
            score = dot / (norm * query_norm)
            doc = self._docs[doc_id]
            ranked.append(SearchResult(doc_id=doc_id, score=score, title=doc.title, url=doc.url))

        ranked.sort(key=lambda item: item.score, reverse=True)
        return ranked[:top_k]

    def bulk_add(self, documents: Iterable[Document]) -> None:
        for doc in documents:
            self.add_document(doc)
