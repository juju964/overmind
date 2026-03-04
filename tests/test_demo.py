from overmind.demo import build_demo_index
from overmind.semantic import SemanticRanker


def test_demo_query_returns_game_docs_first() -> None:
    index = build_demo_index()
    ranker = SemanticRanker(index)
    results = ranker.search("langage pour jeu 2d rapide", top_k=2)
    assert results
    assert results[0].doc_id in {"d1", "d2"}
