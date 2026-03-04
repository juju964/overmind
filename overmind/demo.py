from __future__ import annotations

import argparse
from pprint import pprint

from .indexer import Document, InvertedIndex
from .semantic import SemanticRanker


def build_demo_index() -> InvertedIndex:
    """Build a small offline corpus so users can test Overmind without network access."""
    index = InvertedIndex()
    index.bulk_add(
        [
            Document(
                doc_id="d1",
                title="Créer un jeu 2D rapidement",
                url="demo://guide-2d",
                text=(
                    "Python et Godot permettent de créer un jeu 2D rapidement. "
                    "Le prototypage est rapide et l'ecosysteme est riche."
                ),
            ),
            Document(
                doc_id="d2",
                title="Moteur haute performance",
                url="demo://rust-engine",
                text=(
                    "Rust est excellent pour un moteur de jeu performant avec un controle fin "
                    "de la memoire et de la concurrence."
                ),
            ),
            Document(
                doc_id="d3",
                title="Recette de soupe tomate basilic",
                url="demo://cooking",
                text="Recette cuisine tomate basilic huile olive oignon ail.",
            ),
        ]
    )
    return index


def main() -> None:
    parser = argparse.ArgumentParser(description="Overmind demo (offline semantic search)")
    parser.add_argument("query", help="Question en langage naturel")
    args = parser.parse_args()

    index = build_demo_index()
    ranker = SemanticRanker(index)
    results = ranker.search(args.query, top_k=3)

    print("Top résultats:")
    pprint([
        {"title": r.title, "url": r.url, "score": round(r.score, 4)}
        for r in results
    ])


if __name__ == "__main__":
    main()
