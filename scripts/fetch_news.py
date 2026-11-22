"""Fetch RSS feeds, cross-check stories across sources, write data/news.json."""
import html
import json
import re
from datetime import date
from pathlib import Path

import feedparser

from ai import analyze_all, translate_all

FEEDS = {
    "BBC News": "https://feeds.bbci.co.uk/news/world/rss.xml",
    "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
    "The Guardian": "https://www.theguardian.com/world/rss",
    "NPR": "https://feeds.npr.org/1004/rss.xml",
}

# topic -> keywords found in the headline or summary
TOPICS = {
    "international-law": {"court", "tribunal", "treaty", "icc", "icj", "sanctions", "ruling", "law"},
    "human-rights": {"rights", "refugees", "detention", "prisoners", "protest", "famine"},
    "diplomacy": {"talks", "summit", "ambassador", "minister", "agreement", "trade", "ceasefire"},
}
ROLES = {
    "international-law": ["ir", "law"],
    "human-rights": ["ir", "law"],
    "diplomacy": ["ir"],
    "world": ["ir", "law"],
}

STOPWORDS = {"the", "and", "for", "with", "from", "that", "this", "after", "over",
             "into", "says", "say", "will", "has", "have", "are", "was", "new"}
MIN_SHARED_WORDS = 3   # headlines sharing this many key words = same story
MIN_SOURCES = 2        # a story must appear in at least this many sources
MAX_ITEMS = 10
PER_FEED = 25

OUT_FILE = Path(__file__).resolve().parent.parent / "data" / "news.json"


def keywords(text):
    return {w for w in re.findall(r"[a-z]{3,}", text.lower()) if w not in STOPWORDS}


def clean(text, limit=300):
    text = html.unescape(re.sub(r"<[^>]+>", "", text or "")).strip()
    return text if len(text) <= limit else text[:limit].rsplit(" ", 1)[0] + "…"


def fetch_entries():
    entries = []
    for source, url in FEEDS.items():
        feed = feedparser.parse(url)
        if not feed.entries:
            print(f"Warning: no entries from {source}")
        for e in feed.entries[:PER_FEED]:
            title = clean(e.get("title"))
            entries.append({
                "source": source,
                "title": title,
                "summary": clean(e.get("summary")),
                "url": e.get("link", ""),
                "words": keywords(title),
            })
    return entries


def cluster(entries):
    """Group entries that cover the same story."""
    groups = []
    for e in entries:
        for g in groups:
            if len(e["words"] & g[0]["words"]) >= MIN_SHARED_WORDS:
                g.append(e)
                break
        else:
            groups.append([e])
    return groups


def classify(entry):
    words = keywords(entry["title"] + " " + entry["summary"])
    for topic, keys in TOPICS.items():
        if words & keys:
            return topic
    return "world"


def build_item(group, index, today):
    lead = group[0]
    topic = classify(lead)
    return {
        "id": f"{today}-{index:03d}",
        "date": today,
        "topic": topic,
        "roles": ROLES[topic],
        "title": {"en": lead["title"], "my": ""},
        "details": {"en": lead["summary"], "my": ""},
        "why_it_matters": {"en": "", "my": ""},
        "perspectives": {"en": "", "my": ""},
        "reasoning": {"en": "", "my": ""},
        "source": {"name": lead["source"], "url": lead["url"]},
        "case_id": None,
        "coverage": sorted({e["source"] for e in group}),
    }


def main():
    groups = cluster(fetch_entries())
    confirmed = [g for g in groups if len({e["source"] for e in g}) >= MIN_SOURCES]
    confirmed.sort(key=lambda g: len({e["source"] for e in g}), reverse=True)

    if not confirmed:
        print("No cross-checked stories found. Keeping the existing news.json.")
        return

    today = date.today().isoformat()
    items = [build_item(g, i, today) for i, g in enumerate(confirmed[:MAX_ITEMS], start=1)]
    analyze_all(items)
    translate_all(items)
    OUT_FILE.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(items)} stories to {OUT_FILE}")


if __name__ == "__main__":
    main()
