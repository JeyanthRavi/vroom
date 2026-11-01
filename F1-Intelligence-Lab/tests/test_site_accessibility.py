from pathlib import Path


STATIC = Path(__file__).parents[1] / "src" / "f1_intelligence_lab" / "static"


def test_demo_has_required_accessibility_and_scope_copy():
    page = (STATIC / "model-demo.html").read_text()
    assert 'role="status"' in page
    assert page.count('role="img"') >= 3
    assert "prefers-reduced-motion" in page
    assert ":focus" in page
    assert "What this does:" in page and "What it does not do:" in page
    assert "forward holdout is pending" in page
    assert "methodology.html" in page


def test_every_research_chart_has_adjacent_text_alternative():
    page = (STATIC / "model-demo.html").read_text()
    assert 'aria-labelledby="hazard-alt"' in page and 'id="hazard-alt"' in page
    assert 'aria-labelledby="drift-alt"' in page and 'id="drift-alt"' in page
