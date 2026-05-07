"""News module: fetches headlines from an RSS or Atom feed."""

from __future__ import annotations

from typing import Final
from xml.etree import ElementTree as ET

import httpx

from dashy.http import create_http_client
from dashy.models import Headlines

_DEFAULT_FEED_URL: Final = "https://feeds.bbci.co.uk/news/world/rss.xml"
_MAX_HEADLINES: Final = 5
_ATOM_NAMESPACE: Final = "{http://www.w3.org/2005/Atom}"


def get_headlines(feed_url: str | None = None) -> Headlines:
    """Fetch news headlines from an RSS or Atom feed.

    Returns a list of up to five headline titles on success. Returns an
    empty list on any error (network failure, non-2xx response, malformed
    XML, empty feed). Never raises.

    If ``feed_url`` is ``None``, a default public feed is used.
    """
    url = feed_url if feed_url is not None else _DEFAULT_FEED_URL

    with create_http_client() as client:
        try:
            response = client.get(url)
            response.raise_for_status()
            content = response.content
        except httpx.HTTPError:
            return []

    return _parse_feed(content)


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
