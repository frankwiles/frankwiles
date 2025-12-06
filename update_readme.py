#!/usr/bin/env python3
"""
Update GitHub README with latest blog posts from RSS feed.
"""

import os
import re
import sys
from datetime import datetime, timedelta, timezone

import feedparser


def fetch_feed_entries(url: str, max_posts: int = 5) -> list[dict]:
    """Fetch entries from RSS feed."""
    try:
        feed = feedparser.parse(url)
        entries = []

        for entry in feed.entries[:max_posts]:
            # Get publication date, fallback to current time if not available
            pub_date = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                pub_date = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)

            entries.append(
                {
                    "title": getattr(entry, "title", "No title"),
                    "url": getattr(entry, "link", ""),
                    "summary": getattr(entry, "summary", ""),
                    "description": getattr(entry, "description", ""),
                    "pub_date": pub_date,
                }
            )

        return entries
    except Exception as e:
        print(f"Error fetching feed: {e}", file=sys.stderr)
        return []


def format_date(dt: datetime) -> str:
    """Format datetime as month day, year."""
    return dt.strftime("%B %-d, %Y")


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to specified length."""
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    # Remove extra whitespace
    text = " ".join(text.split())
    if len(text) > max_length:
        text = text[:max_length].rsplit(" ", 1)[0] + "..."
    return text


def format_blog_post(entry: dict) -> str:
    """Format a blog entry as markdown list item."""
    title = entry["title"]
    url = entry["url"]
    date_str = ""
    if entry["pub_date"]:
        date_str = f" - {format_date(entry['pub_date'])}"

    # Use description or summary, whichever is available
    description = entry["description"] or entry["summary"]
    description = truncate_text(description, 100)

    return f"* [{title}]({url}){date_str} - {description}"


def update_readme(
    readme_path: str,
    feed_url: str,
    marker: str,
    max_posts: int = 5,
    check_recent_hours: int = 1,
) -> bool:
    """
    Update README with latest blog posts.

    Returns True if README was updated, False otherwise.
    """
    # Fetch blog entries
    entries = fetch_feed_entries(feed_url, max_posts)
    if not entries:
        print("No entries fetched from feed", file=sys.stderr)
        return False

    # Check if there are any recent posts
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=check_recent_hours)
    has_recent = any(
        entry["pub_date"] and entry["pub_date"] > cutoff_time for entry in entries
    )

    if not has_recent:
        print(f"No posts in the last {check_recent_hours} hours, skipping update")
        return False

    # Read current README
    try:
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading README: {e}", file=sys.stderr)
        return False

    # Find the blog posts section
    start_marker = f"<!-- {marker}_START -->"
    end_marker = f"<!-- {marker}_END -->"

    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker)

    if start_idx == -1 or end_idx == -1:
        print("Blog post markers not found in README", file=sys.stderr)
        return False

    # Generate blog posts markdown
    blog_posts_md = "\n".join(format_blog_post(entry) for entry in entries)

    # Replace content between markers
    new_content = (
        content[: start_idx + len(start_marker)]
        + "\n"
        + blog_posts_md
        + "\n"
        + content[end_idx:]
    )

    # Write updated README
    try:
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Updated README with {len(entries)} blog posts")
        return True
    except Exception as e:
        print(f"Error writing README: {e}", file=sys.stderr)
        return False


def main():
    """Main function."""
    # Get configuration from environment variables
    readme_path = os.getenv("README_PATH", "README.md")
    max_posts = int(os.getenv("MAX_POSTS", "5"))
    check_hours = int(os.getenv("CHECK_RECENT_HOURS", "1"))

    # Main blog posts
    update_readme(
        readme_path,
        "https://frankwiles.com/rss/posts",
        "RECENT_BLOG_POSTS",
        max_posts,
        check_hours,
    )


if __name__ == "__main__":
    main()

