"""Adapted from vc-digital-twins/pitchshow_scraper/investor.py; network-free parsing."""
# pitchshow_scraper/investor.py
"""Parse a Pitch investor profile page into a canonical profile dict."""
import re
from urllib.parse import urljoin, urlsplit
from datetime import datetime, timezone

BASE_URL = "https://www.thepitch.show"
from .jsonld import parse_jsonld, first_of_type


def _now():
    return datetime.now(timezone.utc).isoformat()


def _slug_from_href(href):
    return href.rstrip("/").split("/")[-1]


def extract_theses(soup):
    """Extract 'What X Looks For' thesis quotes with optional season/episode refs."""
    theses = []
    for h in soup.find_all(["h1", "h2"]):
        text = h.get_text(" ", strip=True)
        if "Looks For" in text or "looks for" in text:
            container = h.parent
            for _ in range(6):
                quotes = container.find_all("blockquote") if container else []
                if len(quotes) >= 1:
                    break
                container = container.parent if container else None
            if container:
                ep_pattern = re.compile(r"S(\d+)\s*[·•\-]\s*Ep\s*(\d+)")
                for bq in container.find_all("blockquote"):
                    raw = bq.get_text(" ", strip=True)
                    ep_ref = None
                    m = ep_pattern.search(raw)
                    if m:
                        ep_ref = f"S{m.group(1)} Ep{m.group(2)}"
                        raw = raw[:m.start()] + raw[m.end():]
                    else:
                        for sib in bq.find_all_next(string=True, limit=20):
                            m = ep_pattern.search(sib)
                            if m:
                                ep_ref = f"S{m.group(1)} Ep{m.group(2)}"
                                break
                    quote = raw.strip().strip('“””').strip()
                    if quote:
                        theses.append({"quote": quote, "episode_ref": ep_ref})
            break
    return theses


def extract_investments(soup):
    """Extract investment cards under 'Investments on The Pitch' heading."""
    investments = []
    heading = None
    for h in soup.find_all("h2"):
        if "Investments on The Pitch" in h.get_text(" ", strip=True):
            heading = h
            break
    if not heading:
        return investments

    container = heading.parent
    while container and container.name != "body":
        h3s = container.find_all("h3")
        if len(h3s) >= 1:
            other_h2s = [x for x in container.find_all("h2") if x is not heading]
            if not other_h2s:
                break
        container = container.parent
    if not container:
        return investments

    for h3 in container.find_all("h3"):
        card = h3
        link = None
        for _ in range(8):
            card = card.parent
            if card is None:
                break
            link = card.find("a", href=True)
            if link and len(card.find_all("h3")) == 1:
                break
        if not card or not link:
            continue
        href = link["href"]
        episode_url = urljoin(BASE_URL, href)
        parsed_url = urlsplit(episode_url)
        if parsed_url.scheme != "https" or parsed_url.hostname not in {"www.thepitch.show", "thepitch.show"} or parsed_url.path.startswith("/investors/"):
            continue
        title = h3.get_text(" ", strip=True)
        card_text = card.get_text(" | ", strip=True)
        parts = [p.strip() for p in card_text.split(" | ") if p.strip() and p.strip() != "View Episode"]
        category = check_size = deal_terms = None
        for i, piece in enumerate(parts):
            if piece == title:
                if i > 0:
                    category = parts[i - 1]
                for t in parts[i + 1:]:
                    if re.match(r"^\$[\d\.]+[KMB]?$", t):
                        check_size = t
                    elif "SAFE" in t or "post-money" in t or "Priced Round" in t or "Convertible" in t:
                        deal_terms = t
                break
        investments.append({
            "episode_slug": _slug_from_href(parsed_url.path),
            "episode_url": episode_url,
            "title": title,
            "category": category,
            "check_size": check_size,
            "deal_terms": deal_terms,
        })
    seen, out = set(), []
    for inv in investments:
        if inv["episode_slug"] in seen:
            continue
        seen.add(inv["episode_slug"])
        out.append(inv)
    return out


def extract_faq_stats(jsonld_blocks):
    """Parse FAQ JSON-LD for total-invested, episode count, season range, check sizes."""
    faq = first_of_type(jsonld_blocks, "FAQPage")
    stats = {}
    if not faq:
        return stats
    for item in faq.get("mainEntity", []):
        q = item.get("name", "")
        a = item.get("acceptedAnswer", {}).get("text", "")
        ql = q.lower()
        if "how much" in ql and "invested" in ql:
            m = re.search(r"\$[\d\.]+[KMB]?", a)
            if m:
                stats["total_invested"] = m.group(0)
            m = re.search(r"across\s+(\d+)\s+companies", a)
            if m:
                stats["companies_funded"] = int(m.group(1))
            m = re.search(r"Check sizes range from\s+(\$[\d\.]+[KMB]?)\s+to\s+(\$[\d\.]+[KMB]?)", a)
            if m:
                stats["check_size_min"] = m.group(1)
                stats["check_size_max"] = m.group(2)
        elif "how many episodes" in ql:
            m = re.search(r"(\d+)\s+episodes", a)
            if m:
                stats["episodes_count"] = int(m.group(1))
            m = re.search(r"Season\s+(\d+)\s+through\s+Season\s+(\d+)", a)
            if m:
                stats["season_first"] = int(m.group(1))
                stats["season_last"] = int(m.group(2))
    return stats


def extract_bio(soup):
    """Pull the 'About X' paragraph(s)."""
    for h in soup.find_all(["h2", "h3"]):
        if h.get_text(" ", strip=True).startswith("About"):
            container = h.parent
            while container and container.name != "body":
                paras = container.find_all("p")
                if paras:
                    text = " ".join(p.get_text(" ", strip=True) for p in paras)
                    if len(text) > 50:
                        return text
                container = container.parent
    return None


def parse_investor(soup, url):
    """Parse investor profile soup -> canonical profile dict. Pure w.r.t. network."""
    jsonld = parse_jsonld(soup)
    person = first_of_type(jsonld, "Person") or {}
    stats = extract_faq_stats(jsonld)

    firm = None
    works_for = person.get("worksFor")
    if isinstance(works_for, dict):
        firm = works_for.get("name")
    elif isinstance(works_for, list) and works_for:
        firm = works_for[0].get("name")

    return {
        "id": _slug_from_href(url),
        "name": person.get("name"),
        "firm": firm,
        "profile_url": url,
        "image": person.get("image"),
        "description": person.get("description"),
        "tags": person.get("knowsAbout", []),
        "social_links": person.get("sameAs", []),
        "bio": extract_bio(soup),
        "episodes_count": stats.get("episodes_count"),
        "season_first": stats.get("season_first"),
        "season_last": stats.get("season_last"),
        "companies_funded": stats.get("companies_funded"),
        "total_invested": stats.get("total_invested"),
        "check_size_min": stats.get("check_size_min"),
        "check_size_max": stats.get("check_size_max"),
        "investment_theses": extract_theses(soup),
        "investments": extract_investments(soup),
        "scraped_at": _now(),
    }
