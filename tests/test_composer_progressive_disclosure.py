"""Regression coverage for the compact Home composer."""


def test_composer_hides_secondary_options_by_default(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"<details class=\"mt-2 mb-1\">" in response.data
    assert b"<summary class=\"small fw-semibold text-muted\"" in response.data
    assert b">More options</summary>" in response.data
    assert b'id="conversation_intent"' in response.data
    assert b'id="topics"' in response.data
    assert b'id="scheduleOptions" class="schedule-panel d-none"' in response.data


def test_composer_keeps_primary_actions_compact(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b'id="uploadIcon"' in response.data
    assert b'aria-label="Create a poll"' in response.data
    assert b'id="scheduleIcon"' in response.data
    assert b'class="post-submit">Post</button>' in response.data
