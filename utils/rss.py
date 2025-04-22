import feedparser
from newspaper import Article
from datetime import datetime
from .summarizer import summarize_final_summary
import os
import json

def fetch_rss_entries(rss_url, max_entries=1):
    feed = feedparser.parse(rss_url)

    entries = [entry for entry in feed.entries if entry.get("published_parsed")]

    entries = sorted(entries, key=lambda e: e.published_parsed, reverse=True)

    return entries[:max_entries]



def article_matches_keywords(title: str, description: str, keywords: list) -> bool:
    text = f"{title} {description}".lower()
    return any(keyword.lower() in text for keyword in keywords)

def extract_article_text(url: str) -> str:
    try:
        article = Article(url)
        article.download()
        article.parse()
        return article.text
    except Exception as e:
        return f"Error extracting article: {str(e)}"

def load_processed_blog_links(json_file: str) -> set:
    if os.path.exists(json_file):
        try:
            with open(json_file, mode="r", encoding="utf-8") as f:
                data = json.load(f)
            return {entry["link"] for entry in data if entry.get("source") == "blog"}
        except json.JSONDecodeError:
            return set()
    return set()

def append_blog_summary(link: str, blog_title: str, summary_data: dict, json_file: str, source: str = "blog") -> None:
    entry = {
        "timestamp": datetime.now().isoformat(),
        "link": link,
        "title": blog_title,
        "summary": summary_data,
        "source": source
    }
    if os.path.exists(json_file):
        try:
            with open(json_file, mode="r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            data = []
    else:
        data = []
    data.append(entry)
    with open(json_file, mode="w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def process_blog_feed_for_all_users():
    rss_url = "https://www.analyticsvidhya.com/feed/"
    with open("user_data.json", "r", encoding="utf-8") as f:
        users = json.load(f)

    for user in users:
        username = user["username"]
        keywords = user.get("keywords", [])
        json_file = f"summaries/{username}.json"
        processed_links = load_processed_blog_links(json_file)
        print("here-1")

        print(f"\n📰 Checking RSS for {username}")

        entries = fetch_rss_entries(rss_url)
        print("this is list",entries)
        for entry in entries:
            print("One Entry",entry)
            title = entry.get("title", "")
            description = entry.get("summary", "")
            link = entry.get("link", "")

            if link in processed_links:
                print(f"✅ Already processed: {link}")
                continue

            if not article_matches_keywords(title, description, keywords):
                print(f"No keyword match for: {title}")
                continue

            print(f"🔍 Processing blog: {title}")
            full_text = extract_article_text(link)
            if "Error" in full_text:
                continue

            print('here')

            summary = summarize_final_summary(full_text)
            print('here2')
            blog_title = summary.get("title")
            print(blog_title)
            summary_data = {
                "summary": summary.get("summary"),
                "tags": summary.get("tags"),
                "category": summary.get("category")
            }

            append_blog_summary(link, blog_title, summary_data, json_file)
