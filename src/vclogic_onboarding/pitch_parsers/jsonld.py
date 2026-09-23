"""Adapted from vc-digital-twins/pitchshow_scraper/jsonld.py; network-free parsing."""
"""Shared JSON-LD extraction helpers."""
import json


def parse_jsonld(soup):
    """Return a list of parsed JSON-LD objects from <script type=application/ld+json>."""
    blocks = []
    for script in soup.find_all("script", type="application/ld+json"):
        raw = script.string or script.get_text()
        if not raw:
            continue
        try:
            blocks.append(json.loads(raw))
        except json.JSONDecodeError:
            continue
    return blocks


def first_of_type(blocks, type_name):
    """Return the first JSON-LD dict whose @type matches type_name, else None.

    Handles both string (`"@type": "PodcastEpisode"`) and list
    (`"@type": ["PodcastEpisode", ...]`) forms of @type.
    """
    expanded = []
    def expand(value):
        if isinstance(value, list):
            for item in value:
                expand(item)
        elif isinstance(value, dict):
            expanded.append(value)
            expand(value.get("@graph", []))
    expand(blocks)
    for b in expanded:
        if not isinstance(b, dict):
            continue
        t = b.get("@type")
        if t == type_name or (isinstance(t, list) and type_name in t):
            return b
    return None
