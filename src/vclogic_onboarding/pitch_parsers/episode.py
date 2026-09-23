"""Adapted from vc-digital-twins/pitchshow_scraper/episode.py; network-free parsing."""
# pitchshow_scraper/episode.py
"""Parse a Pitch episode page into a canonical episode dict."""
import re
from datetime import datetime, timezone

BASE_URL = "https://www.thepitch.show"
from .jsonld import parse_jsonld, first_of_type


def _now():
    return datetime.now(timezone.utc).isoformat()


def _slug_from_url(url):
    return url.rstrip("/").split("/")[-1] if url else None


def extract_transcript(soup):
    """Return the speaker-labeled transcript text from div#transcript, or None."""
    node = soup.find("div", id="transcript")
    if not node:
        return None
    text = node.get_text("\n", strip=True)
    if text.startswith("Transcript"):
        text = text[len("Transcript"):].strip()
    text = re.sub(r"\n?Read full transcript.*$", "", text).strip()
    return text


def parse_episode(soup, slug, url=None):
    """Parse episode soup -> canonical episode dict. Pure w.r.t. network."""
    jsonld = parse_jsonld(soup)
    ep = first_of_type(jsonld, "PodcastEpisode") or {}
    actors = ep.get("actor", []) or []
    if isinstance(actors, dict):
        actors = [actors]
    actors = [actor for actor in actors if isinstance(actor, dict)]

    founders = [
        {"name": a.get("name"), "url": a.get("url")}
        for a in actors
        if a.get("description") != "Investor"
    ]
    panel = [
        {"name": a.get("name"), "slug": _slug_from_url(a.get("url")), "url": a.get("url")}
        for a in actors
        if a.get("description") == "Investor"
    ]
    media = ep.get("associatedMedia") or {}

    return {
        "slug": slug,
        "url": url or f"{BASE_URL}/{slug}",
        "name": ep.get("name"),
        "number": ep.get("episodeNumber"),
        "season": ep.get("seasonNumber"),
        "date_published": ep.get("datePublished"),
        "description": ep.get("description"),
        "episode_type": "pitch" if founders else "special",
        "founders": founders,
        "panel": panel,
        "transcript": extract_transcript(soup),
        "audio_url": media.get("contentUrl") if isinstance(media, dict) else None,
        "duration": media.get("duration") if isinstance(media, dict) else None,
        "external_links": ep.get("sameAs", []),
        "scraped_at": _now(),
    }
