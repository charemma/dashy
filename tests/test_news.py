"""Tests for the news module."""

from __future__ import annotations

import httpx
import respx

from dashy.news import get_headlines

_FEED_URL = "https://example.com/feed.xml"


def _rss(items_xml: str) -> bytes:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<rss version="2.0"><channel>'
        "<title>Example feed</title>"
        f"{items_xml}"
        "</channel></rss>"
    ).encode()


def _rss_with_titles(*titles: str) -> bytes:
    items = "".join(f"<item><title>{title}</title></item>" for title in titles)
    return _rss(items)


@respx.mock
def test_news_success_returns_titles_in_order() -> None:
    respx.get(_FEED_URL).mock(
        return_value=httpx.Response(200, content=_rss_with_titles("First", "Second", "Third")),
    )

    assert get_headlines(_FEED_URL) == ["First", "Second", "Third"]


@respx.mock
def test_news_caps_at_five_headlines() -> None:
    titles = [f"Story {i}" for i in range(10)]
    respx.get(_FEED_URL).mock(
        return_value=httpx.Response(200, content=_rss_with_titles(*titles)),
    )

    result = get_headlines(_FEED_URL)

    assert result == titles[:5]
    assert len(result) == 5


@respx.mock
def test_news_returns_fewer_when_feed_has_fewer_items() -> None:
    respx.get(_FEED_URL).mock(
        return_value=httpx.Response(200, content=_rss_with_titles("Only one")),
    )

    assert get_headlines(_FEED_URL) == ["Only one"]


@respx.mock
def test_news_uses_default_feed_when_url_is_none() -> None:
    route = respx.get("https://feeds.bbci.co.uk/news/world/rss.xml").mock(
        return_value=httpx.Response(200, content=_rss_with_titles("Default headline")),
    )

    result = get_headlines()

    assert route.called
    assert result == ["Default headline"]


@respx.mock
def test_news_sends_user_agent_header() -> None:
    route = respx.get(_FEED_URL).mock(
        return_value=httpx.Response(200, content=_rss_with_titles("Story")),
    )

    get_headlines(_FEED_URL)

    sent_user_agent = route.calls.last.request.headers.get("User-Agent", "")
    assert sent_user_agent.startswith("dashy/")


@respx.mock
def test_news_handles_http_404() -> None:
    respx.get(_FEED_URL).mock(return_value=httpx.Response(404))

    assert get_headlines(_FEED_URL) == []


@respx.mock
def test_news_handles_http_500() -> None:
    respx.get(_FEED_URL).mock(return_value=httpx.Response(500))

    assert get_headlines(_FEED_URL) == []


@respx.mock
def test_news_handles_connection_timeout() -> None:
    respx.get(_FEED_URL).mock(side_effect=httpx.ConnectTimeout("timeout"))

    assert get_headlines(_FEED_URL) == []


@respx.mock
def test_news_handles_network_error() -> None:
    respx.get(_FEED_URL).mock(side_effect=httpx.ConnectError("dns failure"))

    assert get_headlines(_FEED_URL) == []


@respx.mock
def test_news_handles_malformed_xml() -> None:
    respx.get(_FEED_URL).mock(
        return_value=httpx.Response(200, content=b"<rss><channel><item>broken"),
    )

    assert get_headlines(_FEED_URL) == []


@respx.mock
def test_news_handles_empty_feed() -> None:
    respx.get(_FEED_URL).mock(return_value=httpx.Response(200, content=_rss("")))

    assert get_headlines(_FEED_URL) == []


@respx.mock
def test_news_skips_items_without_title() -> None:
    items = (
        "<item><title>Has title</title></item>"
        "<item><link>https://example.com/no-title</link></item>"
        "<item><title>Also has title</title></item>"
    )
    respx.get(_FEED_URL).mock(return_value=httpx.Response(200, content=_rss(items)))

    assert get_headlines(_FEED_URL) == ["Has title", "Also has title"]


@respx.mock
def test_news_strips_whitespace_from_titles() -> None:
    items = "<item><title>   Padded title   </title></item>"
    respx.get(_FEED_URL).mock(return_value=httpx.Response(200, content=_rss(items)))

    assert get_headlines(_FEED_URL) == ["Padded title"]


@respx.mock
def test_news_handles_cdata_wrapped_titles() -> None:
    items = "<item><title><![CDATA[Breaking: news & events]]></title></item>"
    respx.get(_FEED_URL).mock(return_value=httpx.Response(200, content=_rss(items)))

    assert get_headlines(_FEED_URL) == ["Breaking: news & events"]


@respx.mock
def test_news_skips_empty_titles() -> None:
    items = (
        "<item><title></title></item>"
        "<item><title>   </title></item>"
        "<item><title>Real title</title></item>"
    )
    respx.get(_FEED_URL).mock(return_value=httpx.Response(200, content=_rss(items)))

    assert get_headlines(_FEED_URL) == ["Real title"]


@respx.mock
def test_news_parses_atom_feed() -> None:
    atom = (
        b'<?xml version="1.0" encoding="UTF-8"?>'
        b'<feed xmlns="http://www.w3.org/2005/Atom">'
        b"<title>Example Atom feed</title>"
        b"<entry><title>Atom one</title></entry>"
        b"<entry><title>Atom two</title></entry>"
        b"</feed>"
    )
    respx.get(_FEED_URL).mock(return_value=httpx.Response(200, content=atom))

    assert get_headlines(_FEED_URL) == ["Atom one", "Atom two"]


@respx.mock
def test_news_ignores_channel_level_title() -> None:
    # The <title> directly under <channel> is the feed name, not a headline.
    items = "<item><title>Item title</title></item>"
    respx.get(_FEED_URL).mock(return_value=httpx.Response(200, content=_rss(items)))

    result = get_headlines(_FEED_URL)

    assert "Example feed" not in result
    assert result == ["Item title"]
