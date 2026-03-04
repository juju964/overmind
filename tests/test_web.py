from overmind.web import _rewrite_links, build_results, normalize_target_url


def test_web_build_results_returns_relevant_items() -> None:
    results = build_results("langage pour jeu 2d rapide")
    assert results
    assert any("jeu" in str(item["title"]).lower() or "moteur" in str(item["title"]).lower() for item in results)


def test_normalize_target_url_accepts_domain_without_scheme() -> None:
    assert normalize_target_url("example.com").startswith("https://")


def test_rewrite_links_routes_navigation_through_proxy() -> None:
    source = '<a href="/docs">Docs</a><img src="/logo.png" />'
    out = _rewrite_links(source, "https://example.com/base")
    assert "/view?url=" in out
    assert "/asset?url=" in out
