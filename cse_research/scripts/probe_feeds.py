"""Live discovery and verification probe for candidate Sri Lankan RSS feeds (Rule R11)."""

import sys
import requests
import feedparser

candidates = {
    "Ada Derana": [
        "http://www.adaderana.lk/rss.php",
        "https://www.adaderana.lk/rss.php",
    ],
    "Daily Mirror": [
        "https://www.dailymirror.lk/rss/breaking-news",
        "https://www.dailymirror.lk/rss/news",
        "https://www.dailymirror.lk/rss/business-news",
        "https://www.dailymirror.lk/rss/front-page",
    ],
    "Newsfirst": [
        "https://www.newsfirst.lk/feed/",
        "https://www.newsfirst.lk/rss/",
        "https://www.newsfirst.lk/feed/rss/",
    ],
    "EconomyNext": [
        "https://economynext.com/feed/",
    ],
    "Daily FT": [
        "https://www.ft.lk/rss/all",
        "https://www.ft.lk/rss/top-story",
        "https://www.ft.lk/rss/financial-services",
        "https://www.ft.lk/rss/news",
    ],
    "The Island": [
        "https://island.lk/feed/",
        "https://island.lk/category/news/feed/",
        "https://island.lk/category/business/feed/",
    ],
    "Sunday Times": [
        "https://www.sundaytimes.lk/feed/",
        "https://www.sundaytimes.lk/rss/news.xml",
        "https://www.sundaytimes.lk/rss/",
    ],
    "Colombo Gazette": [
        "https://colombogazette.com/feed/",
    ],
    "NewsWire": [
        "https://www.newswire.lk/feed/",
    ],
    "Google News Politics": [
        "https://news.google.com/rss/search?q=Sri+Lanka+politics&hl=en-LK&gl=LK&ceid=LK:en",
    ],
    "Google News Economy": [
        "https://news.google.com/rss/search?q=Sri+Lanka+economy+OR+CSE+OR+ASPI&hl=en-LK&gl=LK&ceid=LK:en",
    ],
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 CSE-Research-Bot/1.0"
}

results = []

for name, urls in candidates.items():
    print(f"\n=== Testing {name} ===", flush=True)
    for u in urls:
        try:
            resp = requests.get(u, headers=headers, timeout=6)
            code = resp.status_code
            text = resp.content
            parsed = feedparser.parse(text)
            n_entries = len(parsed.entries)
            feed_title = parsed.feed.get("title", "") if hasattr(parsed, "feed") else ""
            print(f"  URL: {u}", flush=True)
            print(f"    HTTP Status: {code}, Entries: {n_entries}, Title: {feed_title[:50]}", flush=True)
            if n_entries > 0:
                print(f"    Sample Headline: {parsed.entries[0].get('title', '')[:60]}", flush=True)
                print(f"    Sample PubDate: {parsed.entries[0].get('published', 'N/A')}", flush=True)
        except Exception as e:
            print(f"  URL: {u} -> ERROR: {e}", flush=True)

