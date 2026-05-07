"""News module: fetches localized headlines via Google News with BBC fallback."""

from __future__ import annotations

from typing import Final
from xml.etree import ElementTree as ET

import httpx

from dashy.http import create_http_client
from dashy.models import Headlines

_BBC_FEED_URL: Final = "https://feeds.bbci.co.uk/news/world/rss.xml"
_GOOGLE_NEWS_BASE_URL: Final = "https://news.google.com/rss"
_DEFAULT_LANGUAGE: Final = "en"
_MAX_HEADLINES: Final = 5
_ATOM_NAMESPACE: Final = "{http://www.w3.org/2005/Atom}"

# ISO 3166-1 alpha-2 country code -> ISO 639-1 language code.
# Multilingual countries map to their primary/most-common language.
_COUNTRY_LANGUAGE: Final[dict[str, str]] = {
    "AT": "de",
    "BE": "nl",
    "BR": "pt",
    "CH": "de",
    "DE": "de",
    "ES": "es",
    "FR": "fr",
    "GB": "en",
    "GR": "el",
    "IE": "en",
    "IT": "it",
    "JP": "ja",
    "NL": "nl",
    "PL": "pl",
    "PT": "pt",
    "SE": "sv",
    "TR": "tr",
    "US": "en",
}


def get_headlines(country_code: str | None = None) -> Headlines:
    """Fetch news headlines localized to ``country_code``.

    The country code (ISO 3166-1 alpha-2, e.g. ``"DE"``) is used to build
    a Google News RSS URL with matching language and edition. If
    ``country_code`` is ``None`` or Google News cannot be reached, the
    BBC World feed is used as a fallback.

    Returns a list of up to five headline titles. Returns an empty list
    only if both Google News and BBC fail. Never raises.
    """
    if country_code is not None:
        headlines = _fetch_google_news(country_code)
        if headlines:
            return headlines

    return _fetch_feed(_BBC_FEED_URL)


def _fetch_google_news(country_code: str) -> Headlines:
    """Fetch headlines from Google News for a country.

    Returns an empty list on any failure (HTTP error, parse error, empty
    feed). The caller treats an empty result as a signal to fall back.
    """
    language = _country_to_language(country_code)
    url = _build_google_news_url(country_code, language)
    return _fetch_feed(url)


def _fetch_feed(url: str) -> Headlines:
    """Fetch and parse an RSS or Atom feed. Empty list on any error."""
    with create_http_client() as client:
        try:
            response = client.get(url)
            response.raise_for_status()
            content = response.content
        except httpx.HTTPError:
            return []

    return _parse_feed(content)


def _country_to_language(country_code: str) -> str:
    """Map an ISO 3166-1 alpha-2 country code to a language code.

    Lookup is case-insensitive. Unknown countries fall back to English.
    """
    return _COUNTRY_LANGUAGE.get(country_code.upper(), _DEFAULT_LANGUAGE)


def _build_google_news_url(country_code: str, language: str) -> str:
    """Construct a Google News RSS URL with localization parameters.

    Format: ``https://news.google.com/rss?hl={lang}&gl={CC}&ceid={CC}:{lang}``
    """
    cc = country_code.upper()
    return f"{_GOOGLE_NEWS_BASE_URL}?hl={language}&gl={cc}&ceid={cc}:{language}"


def _parse_feed(xml_content: bytes) -> Headlines:
    """Parse RSS 2.0 or Atom XML and return up to five headline titles.

    Returns an empty list if the XML is malformed or contains no usable
    titles. Items missing a ``<title>`` element are skipped, not treated
    as fatal.
    """
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError:
        return []

    titles: list[str] = []
    for title_element in _iter_title_elements(root):
        text = _extract_text(title_element)
        if text:
            titles.append(text)
        if len(titles) >= _MAX_HEADLINES:
            break

    return titles


def _iter_title_elements(root: ET.Element) -> list[ET.Element]:
    """Yield item title elements from an RSS or Atom document.

    For RSS 2.0 this is ``channel/item/title``; for Atom it is
    ``entry/title`` with the Atom namespace. The channel- or feed-level
    title is intentionally excluded.
    """
    rss_titles = root.findall("./channel/item/title")
    if rss_titles:
        return rss_titles

    return root.findall(f"./{_ATOM_NAMESPACE}entry/{_ATOM_NAMESPACE}title")


def _extract_text(element: ET.Element) -> str:
    """Return the stripped text content of an element, or ``""`` if empty.

    Handles plain text and CDATA-wrapped content uniformly via
    ``itertext``, which concatenates all descendant text nodes.
    """
    text = "".join(element.itertext())
    return text.strip()
