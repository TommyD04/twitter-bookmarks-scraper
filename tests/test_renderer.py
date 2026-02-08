from scraper.renderer import render_bookmark, bookmark_filename


def make_bookmark(**overrides):
    defaults = {
        "id": "123",
        "text": "Hello world",
        "author": "Test User (@testuser)",
        "handle": "testuser",
        "created_at": "2024-03-15",
        "likes": 450,
        "retweets": 83,
        "replies": 12,
        "url": "https://x.com/testuser/status/123",
        "has_media": False,
        "is_reply": False,
        "in_reply_to": None,
    }
    defaults.update(overrides)
    return defaults


def test_render_bookmark_frontmatter():
    bm = make_bookmark()
    md = render_bookmark(bm)

    assert md.startswith("---\n")
    assert 'author: "Test User (@testuser)"' in md
    assert 'handle: "testuser"' in md
    assert 'tweet_url: "https://x.com/testuser/status/123"' in md
    assert 'date: "2024-03-15"' in md
    assert "likes: 450" in md
    assert "retweets: 83" in md
    assert "replies: 12" in md
    assert "is_thread: false" in md
    assert "thread_length: 1" in md


def test_render_bookmark_body():
    bm = make_bookmark()
    md = render_bookmark(bm)

    assert "# @testuser — 2024-03-15" in md
    assert "Hello world" in md


def test_render_bookmark_special_characters():
    bm = make_bookmark(text='She said "hello" & goodbye\\n')
    md = render_bookmark(bm)

    # Should not break YAML — text is in body, not frontmatter values
    assert "---" in md
    assert 'She said "hello" & goodbye\\n' in md


def test_bookmark_filename():
    bm = make_bookmark()
    assert bookmark_filename(bm) == "@testuser-123.md"


def test_bookmark_filename_different_handle():
    bm = make_bookmark(handle="other_user", id="456")
    assert bookmark_filename(bm) == "@other_user-456.md"


def test_render_thread():
    bm = make_bookmark(text="Reply text", is_reply=True, in_reply_to="98")
    thread = [
        make_bookmark(id="98", text="Root tweet", handle="root_user",
                      url="https://x.com/root_user/status/98",
                      is_reply=False, in_reply_to=None),
        make_bookmark(id="99", text="Middle tweet", handle="mid_user",
                      url="https://x.com/mid_user/status/99",
                      is_reply=True, in_reply_to="98"),
        bm,
    ]
    md = render_bookmark(bm, thread=thread)

    assert "is_thread: true" in md
    assert "thread_length: 3" in md
    assert "## Tweet 1 of 3 (thread start)" in md
    assert "Root tweet" in md
    assert "## Tweet 2 of 3" in md
    assert "Middle tweet" in md
    assert "## Tweet 3 of 3 (bookmarked)" in md
    assert "Reply text" in md


def test_render_thread_single_no_change():
    """A thread of length 1 renders the same as no thread."""
    bm = make_bookmark()
    md_no_thread = render_bookmark(bm)
    md_single_thread = render_bookmark(bm, thread=[bm])

    assert md_no_thread == md_single_thread
    assert "is_thread: false" in md_single_thread
    assert "thread_length: 1" in md_single_thread


def test_render_thread_none_same_as_no_thread():
    bm = make_bookmark()
    md_none = render_bookmark(bm, thread=None)
    md_no_arg = render_bookmark(bm)
    assert md_none == md_no_arg
