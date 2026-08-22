from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(name):
    return (ROOT / name).read_text(encoding="utf-8")


def test_public_shell_exposes_keyboard_and_landmark_contract(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b'<a class="skip-link" href="#main-content">Skip to content</a>' in response.data
    assert b'<main class="content-column" id="main-content" tabindex="-1">' in response.data
    assert b'aria-label="Primary navigation"' in response.data
    assert b'aria-label="Mobile navigation"' in response.data
    assert b'aria-current="page"' in response.data


def test_login_navigation_identifies_the_current_page(client):
    response = client.get("/login")

    assert response.status_code == 200
    assert b'href="/login" aria-current="page"' in response.data


def test_composer_controls_expose_relationship_and_state(client):
    response = client.get("/")

    assert b'aria-controls="image"' in response.data
    assert b'aria-controls="scheduleOptions" aria-expanded="false"' in response.data
    assert b"scheduleIcon.setAttribute('aria-expanded', String(!isExpanded))" in response.data


def test_design_system_keeps_focus_and_motion_preferences_visible():
    styles = read("static/css/styles.css")

    assert ":focus-visible" in styles
    assert "outline: 3px solid var(--accent-dark) !important" in styles
    assert '.nav-pill[aria-current="page"]' in styles
    assert '.mobile-nav a[aria-current="page"]' in styles
    assert "@media (prefers-reduced-motion: reduce)" in styles
    assert "animation-duration: .01ms !important" in styles
    assert "animation-iteration-count: 1 !important" in styles


def test_accessibility_guide_does_not_claim_unverified_compliance():
    guide = read("docs/accessibility.md")

    assert "does not claim WCAG conformance" in guide
    assert "keyboard-only" in guide
    assert "screen reader" in guide
    assert "Automated checks cannot establish conformance" in guide
