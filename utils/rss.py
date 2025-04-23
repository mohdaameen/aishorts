import feedparser
from newspaper import Article
from datetime import datetime
from typing import Tuple
from .summarizer import summarize_final_summary_analyticalvidya
from models.schemas import SummaryTagMap, UserTagMap, UserCredential, Summary, Tag, Database
import os
import json

db=Database()

def fetch_rss_entries(rss_url, max_entries=1):
    feed = feedparser.parse(rss_url)

    entries = [entry for entry in feed.entries if entry.get("published_parsed")]

    entries = sorted(entries, key=lambda e: e.published_parsed, reverse=True)

    return entries[:max_entries]

def extract_article_text(url: str) -> Tuple[bool, str]:
    try:
        article = Article(url)
        article.download()
        article.parse()
        return True, article.text
    except Exception as e:
        return False, f"Error extracting article: {str(e)}"


def process_blog_feed_for_all_users():
    print(f"🕒 process_all_users_analyticsvidya() triggered at {datetime.now()}")
    session = db.get_session()

    try:
        rss_url = "https://www.analyticsvidhya.com/feed/"
        entries = fetch_rss_entries(rss_url)
        for entry in entries:
            print("One Entry: ",entry)
            title = entry.get("title", "")
            description = entry.get("summary", "")
            link = entry.get("link", "")

            existing_summary = session.query(Summary).filter_by(link=link).first()
            if existing_summary:
                print(f"✅ Already processed: {link}")
                continue

            print(f"🔍 Processing blog: {title}")

            success, full_text = extract_article_text(link)
            if not success:
                print(f"❌ Failed to extract article: {full_text}")
                continue
    
    

            summary_output = summarize_final_summary_analyticalvidya(full_text)
            print(summary_output)
            print("Summary fetched by AI: ",summary_output)
            blog_title = summary_output.get("title")
            print("Title of the blog: ",blog_title)

            new_summary = Summary(
                    title=summary_output.get("title"),
                    summary=summary_output.get("summary"),
                    source="analyticsvidhya",
                    link=link,
                    category=summary_output.get("category")
                )

            session.add(new_summary)
            session.flush()

            tag_names = summary_output.get("tags", [])
            for tag_name in tag_names:
                tag_name = tag_name.lower().strip()
                    
                tag = session.query(Tag).filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    session.add(tag)
                    session.flush()
                new_summary.tags.append(tag)

            print(f"✅ Saved summary for blog: {link}")

        session.commit()
        print("✅ All summaries stored in DB.")

    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
    finally:
        session.close()
            


       
        
        

