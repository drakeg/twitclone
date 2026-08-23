from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(name):
    return (ROOT / name).read_text(encoding="utf-8")


def test_accessibility_stylesheet_is_loaded_after_visual_styles():
    base = read("templates/base.html")

    visual = "css/styles.css"
    accessibility = "css/accessibility.css"
    assert visual in base
    assert accessibility in base
    assert base.index(visual) < base.index(accessibility)


def test_narrow_layout_has_reflow_safeguards():
    css = read("static/css/accessibility.css")

    assert "@media (max-width: 600px)" in css
    assert ".schedule-panel" in css
    assert "grid-template-columns: minmax(0, 1fr)" in css
    assert ".page-header" in css
    assert "flex-wrap: wrap" in css
    assert "overflow-wrap: anywhere" in css
    assert ".table-responsive" in css
    assert "overflow-x: auto" in css


def test_timeline_labeled_controls_hide_decorative_icons():
    template = read("templates/index.html")

    assert 'aria-label="Repost"><i class="fa-solid fa-retweet" aria-hidden="true"' in template
    assert 'aria-label="Quote"><i class="fa-solid fa-quote-right" aria-hidden="true"' in template
    assert 'aria-label="Bookmark"><i class="fa-regular fa-bookmark" aria-hidden="true"' in template
    assert 'aria-label="Report content" title="Report"><i class="fa-regular fa-flag" aria-hidden="true"' in template
    assert '<i class="fa-solid fa-retweet" aria-hidden="true"></i> Retweeted from' in template
    assert '<i class="fa-solid fa-quote-left" aria-hidden="true"></i> Quoted' in template


def test_accessibility_docs_record_manual_screen_reader_gate_without_claiming_conformance():
    docs = read("docs/accessibility.md")

    assert "Manual assistive-technology gate" in docs
    assert "NVDA + current Firefox or Chrome" in docs
    assert "VoiceOver + current Safari" in docs
    assert "200% and 400% browser zoom" in docs
    assert "must never be presented as proof of conformance" in docs
    assert "1.4.10 Reflow" in docs
    assert "4.1.2 Name, Role, Value" in docs
