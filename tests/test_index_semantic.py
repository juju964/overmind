from overmind.indexer import Document, InvertedIndex
from overmind.semantic import SemanticRanker


def _build_index() -> InvertedIndex:
    index = InvertedIndex()
    index.bulk_add(
        [
            Document("1", "Python Game", "https://a", "Python is great for building a 2D game quickly"),
            Document("2", "Rust Engine", "https://b", "Rust language gives high performance for game engine"),
            Document("3", "Cooking", "https://c", "Tomato soup and basil recipe"),
        ]
    )
    return index


def test_tfidf_search_prefers_relevant_doc() -> None:
    index = _build_index()
    results = index.search("best language for 2d game")
    assert results
    assert results[0].doc_id in {"1", "2"}


def test_semantic_search_filters_noise() -> None:
    index = _build_index()
    ranker = SemanticRanker(index)
    results = ranker.search("fast 2d game language", top_k=2)
    ids = [r.doc_id for r in results]
    assert "3" not in ids
