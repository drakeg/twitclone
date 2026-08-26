from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_profile_uses_non_overlapping_responsive_toolbar():
    template = (ROOT / "templates/profile.html").read_text(encoding="utf-8")
    assert 'class="profile-toolbar"' in template
    assert '.profile-toolbar .profile-actions' in template
    assert 'flex-wrap: wrap' in template
    assert 'margin-top: 66px' in template
    assert '@media (max-width: 520px)' in template
    assert '@media (max-width: 390px)' in template


def test_profile_actions_are_nested_with_avatar_inside_toolbar():
    template = (ROOT / "templates/profile.html").read_text(encoding="utf-8")
    toolbar_start = template.index('<div class="profile-toolbar">')
    avatar = template.index('class="profile-avatar"', toolbar_start)
    actions = template.index('<div class="profile-actions">', avatar)
    toolbar_end = template.index('</div>\n<h2 class="profile-name">', actions)
    assert toolbar_start < avatar < actions < toolbar_end
