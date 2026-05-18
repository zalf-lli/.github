#!/usr/bin/env python3
"""Fetch RSS feeds from iat-dml/iat-dml.github.io and inject them into profile/README.md."""

import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

# Read directly from the gh-pages branch via raw.githubusercontent.com
# to avoid depending on the live GitHub Pages site being reachable.
NEWS_FEED_URL = "https://raw.githubusercontent.com/iat-dml/iat-dml.github.io/gh-pages/news.xml"
PROJECTS_FEED_URL = "https://raw.githubusercontent.com/iat-dml/iat-dml.github.io/gh-pages/projects.xml"
README_PATH = "profile/README.md"
MAX_ITEMS = 5


def fetch_feed(url: str) -> ET.Element:
    with urllib.request.urlopen(url, timeout=15) as response:
        return ET.fromstring(response.read())


def format_date(pub_date: str) -> str:
    try:
        dt = parsedate_to_datetime(pub_date)
        return dt.strftime("%d %b %Y")
    except Exception:
        return pub_date


def strip_html(text: str) -> str:
    """Very lightweight HTML tag stripper for feed descriptions."""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > 160:
        text = text[:157].rstrip() + "..."
    return text


def build_news_section(root: ET.Element) -> str:
    lines = []
    items = root.findall(".//item")[:MAX_ITEMS]
    for item in items:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_date = item.findtext("pubDate") or ""
        date_str = format_date(pub_date) if pub_date else ""
        date_badge = f" <sub>{date_str}</sub>" if date_str else ""
        lines.append(f"- 📄 **[{title}]({link})**{date_badge}")
    return "\n".join(lines)


def build_projects_section(root: ET.Element) -> str:
    lines = []
    items = root.findall(".//item")[:MAX_ITEMS]
    for item in items:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        raw_desc = item.findtext("description") or ""
        desc = strip_html(raw_desc)
        lines.append(f"- 🔧 **[{title}]({link})**")
        if desc:
            lines.append(f"  {desc}")
    return "\n".join(lines)


def inject_section(content: str, start_marker: str, end_marker: str, new_body: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    replacement = (
        f"{start_marker}\n"
        f"{new_body}\n\n"
        f"<sub>Last updated: {timestamp}</sub>\n"
        f"{end_marker}"
    )
    pattern = re.compile(
        re.escape(start_marker) + r".*?" + re.escape(end_marker),
        re.DOTALL,
    )
    return pattern.sub(replacement, content)


def main():
    print("Fetching news feed...")
    news_root = fetch_feed(NEWS_FEED_URL)
    print("Fetching projects feed...")
    projects_root = fetch_feed(PROJECTS_FEED_URL)

    news_md = build_news_section(news_root)
    projects_md = build_projects_section(projects_root)

    with open(README_PATH, "r", encoding="utf-8") as fh:
        readme = fh.read()

    readme = inject_section(readme, "<!-- NEWS-FEED:START -->", "<!-- NEWS-FEED:END -->", news_md)
    readme = inject_section(readme, "<!-- PROJECTS-FEED:START -->", "<!-- PROJECTS-FEED:END -->", projects_md)

    with open(README_PATH, "w", encoding="utf-8") as fh:
        fh.write(readme)

    print("README updated successfully.")


if __name__ == "__main__":
    main()
