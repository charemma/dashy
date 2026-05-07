"""Tests for the news module."""

from __future__ import annotations

import httpx
import pytest
import respx

from dashy.news import (
    _build_google_news_url,
    _country_to_language,
    get_headlines,
)

_BBC_URL = "https://feeds.bbci.co.uk/news/world/rss.xml"
_GOOGLE_BASE = "https://news.google.com/rss"


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


def _google_url(country: str, language: str) -> str:
    return f"{_GOOGLE_BASE}?hl={language}&gl={country}&ceid={country}:{language}"


# ---------------------------------------------------------------------------
# Country-to-language mapping
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("country", "expected_language"),
    [
        ("DE", "de"),
        ("GR", "el"),
        ("US", "en"),
        ("GB", "en"),
        ("FR", "fr"),
        ("ES", "es"),
        ("IT", "it"),
        ("NL", "nl"),
        ("AT", "de"),
        ("CH", "de"),
        ("JP", "ja"),
    ],
)
def test_country_to_language_known_countries(country: str, expected_language: str) -> None:
    assert _country_to_language(country) == expected_language


def test_country_to_language_unknown_falls_back_to_english() -> None:
    assert _country_to_language("XX") == "en"
    assert _country_to_language("ZZ") == "en"


def test_country_to_language_is_case_insensitive() -> None:
    assert _country_to_language("de") == "de"
    assert _country_to_language("Gr") == "el"


# ---------------------------------------------------------------------------
# Google News URL construction
# ---------------------------------------------------------------------------


def test_build_google_news_url_for_germany() -> None:
    assert (
        _build_google_news_url("DE", "de")
        == "https://news.google.com/rss?hl=de&gl=DE&ceid=DE:de"
    )


def test_build_google_news_url_uppercases_country_code() -> None:
    assert (
        _build_google_news_url("de", "de")
        == "https://news.google.com/rss?hl=de&gl=DE&ceid=DE:de"
    )


# ---------------------------------------------------------------------------
# get_headlines: localized fetch
# ---------------------------------------------------------------------------


@respx.mock
def test_get_headlines_fetches_localized_feed_for_known_country() -> None:
    route = respx.get(_google_url("DE", "de")).mock(
        return_value=httpx.Response(200, content=_rss_with_titles("Erste", "Zweite")),
    )

    result = get_headlines("DE")

    assert route.called
    assert result == ["Erste", "Zweite"]


@respx.mock
def test_get_headlines_uses_english_url_for_unknown_country() -> None:
    route = respx.get(_google_url("XX", "en")).mock(
        return_value=httpx.Response(200, content=_rss_with_titles("Headline")),
    )

    result = get_headlines("XX")

    assert route.called
    assert result == ["Headline"]


@respx.mock
def test_get_headlines_caps_at_five() -> None:
    titles = [f"Story {i}" for i in range(10)]
    respx.get(_google_url("US", "en")).mock(
        return_value=httpx.Response(200, content=_rss_with_titles(*titles)),
    )

    result = get_headlines("US")

    assert result == titles[:5]


# ---------------------------------------------------------------------------
# Fallback: country_code is None
# ---------------------------------------------------------------------------


@respx.mock
def test_get_headlines_uses_bbc_when_country_code_is_none() -> None:
    bbc_route = respx.get(_BBC_URL).mock(
        return_value=httpx.Response(200, content=_rss_with_titles("BBC headline")),
    )

    result = get_headlines(None)

    assert bbc_route.called
    assert result == ["BBC headline"]


@respx.mock
def test_get_headlines_does_not_call_google_when_country_code_is_none() -> None:
    google_route = respx.get(url__startswith=_GOOGLE_BASE).mock(
        return_value=httpx.Response(200, content=_rss_with_titles("Should not be called")),
    )
    respx.get(_BBC_URL).mock(
        return_value=httpx.Response(200, content=_rss_with_titles("BBC")),
    )

    get_headlines(None)

    assert not google_route.called


# ---------------------------------------------------------------------------
# Fallback: Google News failure -> BBC
# ---------------------------------------------------------------------------


@respx.mock
def test_get_headlines_falls_back_to_bbc_on_google_404() -> None:
    respx.get(_google_url("DE", "de")).mock(return_value=httpx.Response(404))
    bbc_route = respx.get(_BBC_URL).mock(
        return_value=httpx.Response(200, content=_rss_with_titles("BBC fallback")),
    )

    result = get_headlines("DE")

    assert bbc_route.called
    assert result == ["BBC fallback"]


@respx.mock
def test_get_headlines_falls_back_to_bbc_on_google_500() -> None:
    respx.get(_google_url("DE", "de")).mock(return_value=httpx.Response(500))
    bbc_route = respx.get(_BBC_URL).mock(
        return_value=httpx.Response(200, content=_rss_with_titles("BBC fallback")),
    )

    result = get_headlines("DE")

    assert bbc_route.called
    assert result == ["BBC fallback"]


@respx.mock
def test_get_headlines_falls_back_to_bbc_on_google_timeout() -> None:
    respx.get(_google_url("DE", "de")).mock(side_effect=httpx.ConnectTimeout("timeout"))
    bbc_route = respx.get(_BBC_URL).mock(
        return_value=httpx.Response(200, content=_rss_with_titles("BBC fallback")),
    )

    result = get_headlines("DE")

    assert bbc_route.called
    assert result == ["BBC fallback"]


@respx.mock
def test_get_headlines_falls_back_to_bbc_on_malformed_google_xml() -> None:
    respx.get(_google_url("DE", "de")).mock(
        return_value=httpx.Response(200, content=b"<rss><channel><item>broken"),
    )
    bbc_route = respx.get(_BBC_URL).mock(
        return_value=httpx.Response(200, content=_rss_with_titles("BBC fallback")),
    )

    result = get_headlines("DE")

    assert bbc_route.called
    assert result == ["BBC fallback"]


@respx.mock
def test_get_headlines_falls_back_to_bbc_on_empty_google_feed() -> None:
    respx.get(_google_url("DE", "de")).mock(
        return_value=httpx.Response(200, content=_rss("")),
    )
    bbc_route = respx.get(_BBC_URL).mock(
        return_value=httpx.Response(200, content=_rss_with_titles("BBC fallback")),
    )

    result = get_headlines("DE")

    assert bbc_route.called
    assert result == ["BBC fallback"]


# ---------------------------------------------------------------------------
# Both sources fail
# ---------------------------------------------------------------------------


@respx.mock
def test_get_headlines_returns_empty_when_both_sources_fail() -> None:
    respx.get(_google_url("DE", "de")).mock(return_value=httpx.Response(503))
    respx.get(_BBC_URL).mock(return_value=httpx.Response(503))

    assert get_headlines("DE") == []


@respx.mock
def test_get_headlines_returns_empty_when_bbc_fails_and_country_is_none() -> None:
    respx.get(_BBC_URL).mock(side_effect=httpx.ConnectError("dns failure"))

    assert get_headlines(None) == []


# ---------------------------------------------------------------------------
# Behavioural tests inherited from prior implementation
# ---------------------------------------------------------------------------


@respx.mock
def test_get_headlines_sends_user_agent_header() -> None:
    route = respx.get(_google_url("US", "en")).mock(
        return_value=httpx.Response(200, content=_rss_with_titles("Story")),
    )

    get_headlines("US")

    sent_user_agent = route.calls.last.request.headers.get("User-Agent", "")
    assert sent_user_agent.startswith("dashy/")


@respx.mock
def test_get_headlines_strips_whitespace_from_titles() -> None:
    items = "<item><title>   Padded title   </title></item>"
    respx.get(_google_url("US", "en")).mock(
        return_value=httpx.Response(200, content=_rss(items)),
    )
    respx.get(_BBC_URL).mock(return_value=httpx.Response(503))

    assert get_headlines("US") == ["Padded title"]


@respx.mock
def test_get_headlines_handles_cdata_titles() -> None:
    items = "<item><title><![CDATA[Breaking: news & events]]></title></item>"
    respx.get(_google_url("US", "en")).mock(
        return_value=httpx.Response(200, content=_rss(items)),
    )
    respx.get(_BBC_URL).mock(return_value=httpx.Response(503))

    assert get_headlines("US") == ["Breaking: news & events"]


@respx.mock
def test_get_headlines_skips_items_without_title() -> None:
    items = (
        "<item><title>Has title</title></item>"
        "<item><link>https://example.com/no-title</link></item>"
        "<item><title>Also has title</title></item>"
    )
    respx.get(_google_url("US", "en")).mock(
        return_value=httpx.Response(200, content=_rss(items)),
    )
    respx.get(_BBC_URL).mock(return_value=httpx.Response(503))

    assert get_headlines("US") == ["Has title", "Also has title"]


@respx.mock
def test_get_headlines_parses_atom_feed() -> None:
    atom = (
        b'<?xml version="1.0" encoding="UTF-8"?>'
        b'<feed xmlns="http://www.w3.org/2005/Atom">'
        b"<title>Example Atom feed</title>"
        b"<entry><title>Atom one</title></entry>"
        b"<entry><title>Atom two</title></entry>"
        b"</feed>"
    )
    respx.get(_google_url("US", "en")).mock(
        return_value=httpx.Response(200, content=atom),
    )

    assert get_headlines("US") == ["Atom one", "Atom two"]


@respx.mock
def test_get_headlines_ignores_channel_level_title() -> None:
    items = "<item><title>Item title</title></item>"
    respx.get(_google_url("US", "en")).mock(
        return_value=httpx.Response(200, content=_rss(items)),
    )

    result = get_headlines("US")

    assert "Example feed" not in result
    assert result == ["Item title"]
