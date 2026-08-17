from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_home_uses_package_owned_styles_and_semantic_shell(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b'href="/static/css/styles.css"' in response.data
    assert b'href="/static/favicon.svg"' in response.data
    assert b'class="primary-nav"' in response.data
    assert b'class="content-column"' in response.data
    assert b'class="discovery-rail"' in response.data
    assert b'class="mobile-nav"' in response.data
    assert b'Skip to content' in response.data
    assert b'Ripple' in response.data
    assert b'TwitClone' not in response.data


def test_timeline_preserves_composer_and_action_contract(client):
    response = client.get("/")

    assert b'id="composer"' in response.data
    assert b'name="content"' in response.data
    assert b'maxlength="144"' in response.data
    assert b'id="uploadIcon"' in response.data
    assert b'id="scheduleIcon"' in response.data


def test_design_system_defines_identity_and_responsive_breakpoints():
    styles = (ROOT / "static/css/styles.css").read_text(encoding="utf-8")

    assert "--accent: #635bff" in styles
    assert ".app-shell" in styles
    assert ".post-card" in styles
    assert "@media (max-width: 820px)" in styles
    assert "prefers-reduced-motion" in styles


def test_authentication_pages_use_focused_layout(client):
    for path in ("/login", "/register"):
        response = client.get(path)

        assert response.status_code == 200
        assert b'<body class="auth-page">' in response.data
        assert b'class="surface-card auth-card"' in response.data
        assert b'Ripple' in response.data
        assert b'TwitClone' not in response.data
