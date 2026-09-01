from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(name):
    return (ROOT / name).read_text(encoding="utf-8")


def relative_luminance(hex_color):
    channels = [int(hex_color[index : index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [
        channel / 12.92
        if channel <= 0.04045
        else ((channel + 0.055) / 1.055) ** 2.4
        for channel in channels
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast_ratio(first, second):
    lighter, darker = sorted(
        (relative_luminance(first), relative_luminance(second)), reverse=True
    )
    return (lighter + 0.05) / (darker + 0.05)


def test_secondary_pages_start_with_level_one_headings():
    expected = {
        "templates/create_poll.html": "<h1>Create Poll</h1>",
        "templates/quote.html": "<h1>Quote post</h1>",
        "templates/reply.html": "<h1>Reply to {{ message.sender.username }}</h1>",
        "templates/search_results.html": '<h1 id="search-results-heading">',
        "templates/followers.html": "<h1>{{ user.username }}'s Followers</h1>",
        "templates/following.html": "<h1>{{ user.username }}'s Following</h1>",
    }

    for template, heading in expected.items():
        assert heading in read(template)


def test_dynamic_poll_choices_are_named_focused_and_announced():
    template = read("templates/create_poll.html")

    assert ">Add choice</button>" in template
    assert '<legend class="form-label">Choices</legend>' in template
    assert '<legend class="form-label">Duration</legend>' in template
    assert 'aria_label="Choice " ~ loop.index' in template
    assert 'id="choice-status" class="visually-hidden" role="status"' in template
    assert 'aria-label="Choice ${choiceCount}"' in template
    assert "choiceDiv.querySelector('input').focus()" in template
    assert "choiceStatus.textContent = `Choice ${choiceCount} added.`" in template
    assert "addChoice.disabled = true" in template


def test_repeated_avatars_and_message_icons_do_not_add_noise():
    assert 'alt=""' in read("templates/followers.html")
    assert 'alt=""' in read("templates/following.html")

    messages = read("templates/messages.html")
    assert 'aria-label="Delete message from {{ message.sender.username }}"' in messages
    assert 'aria-label="Delete message sent to {{ message.receiver.username }}"' in messages
    assert messages.count('aria-hidden="true"') >= 3


def test_account_tables_have_captions_and_explicit_headers():
    billing = read("templates/billing.html")
    membership = read("templates/membership.html")

    assert "Features included with each Ripple plan" in billing
    assert billing.count('scope="col"') >= 4
    assert "Your subscription history" in membership
    assert membership.count('scope="col"') >= 4
    assert 'scope="row">{{ subscription.plan.name }}' in membership


def test_core_text_color_pairs_meet_normal_text_contrast():
    assert contrast_ratio("#17152b", "#ffffff") >= 4.5
    assert contrast_ratio("#706e80", "#ffffff") >= 4.5
    assert contrast_ratio("#635bff", "#ffffff") >= 4.5
    assert contrast_ratio("#4b43d8", "#f1efff") >= 4.5
