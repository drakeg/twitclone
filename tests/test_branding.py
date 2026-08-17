from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_user_facing_brand_is_ripple(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"Ripple" in response.data
    assert b"TwitClone" not in response.data


def test_brand_docs_use_ripple_name():
    for relative_path in (
        "README.md",
        "docs/PRODUCT_VISION.md",
        "docs/design-system.md",
    ):
        content = (ROOT / relative_path).read_text(encoding="utf-8")
        assert "Ripple" in content
