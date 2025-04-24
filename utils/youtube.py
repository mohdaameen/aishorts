import os
import json
import requests
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi
from datetime import datetime
from .summarizer import summarize_final_summary_youtube
from models.schemas import SummaryTagMap, UserTagMap, UserCredential, Summary, Tag, Database
from sqlalchemy.exc import IntegrityError

load_dotenv()

db = Database()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

PREDEFINED_CHANNELS=["UCsQoiOrh7jzKmE8NBofhTnQ","UChpleBmo18P08aKCIgti38g","UCXZCJLdBC09xxGZ6gcdrc6A","UChpleBmo18P08aKCIgti38g", "UCC-lyoTfSrcJzA1ab3APAgw"]

def get_uploads_playlist_id(channel_id: str) -> str:
    url = f"https://www.googleapis.com/youtube/v3/channels?part=contentDetails&id={channel_id}&key={YOUTUBE_API_KEY}"
    response = requests.get(url).json()
    return response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

def get_latest_videos_from_channel(channel_id: str, max_results=1) -> list:
    """
    Get the latest videos from a YouTube channel.

    Args:
        channel_id (str): The ID of the channel.
        max_results (int, optional): The maximum number of videos to return. Defaults to 3.

    Returns:
        list: A list of dictionaries with the video ID, title, and description.
    """
    playlist_id = get_uploads_playlist_id(channel_id)
    url = f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&maxResults={max_results}&playlistId={playlist_id}&key={YOUTUBE_API_KEY}"
    response = requests.get(url).json()
    videos = []
    for item in response.get("items", []):
        snippet = item["snippet"]
        video_id = snippet["resourceId"]["videoId"]
        title = snippet["title"]
        description = snippet.get("description", "")
        videos.append({"video_id": video_id, "title": title, "description": description})
    return videos


def fetch_youtube_transcript(video_id: str) -> list:
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return transcript
    except Exception as e:
        return [{"text": f"Error fetching transcript: {str(e)}"}]



def process_all_users():
    print(f"🕒 process_all_users_youtube() triggered at {datetime.now()}")
    session = db.get_session()

    try:
        for channel_id in PREDEFINED_CHANNELS:
            print(f"\n📺 Checking channel: {channel_id}")
            videos = get_latest_videos_from_channel(channel_id)

            for video in videos:
                video_id = video["video_id"]
                title = video["title"]
                description = video["description"]

                existing_summary = session.query(Summary).filter_by(link=f"https://www.youtube.com/watch?v={video_id}").first()
                if existing_summary:
                    print(f"✅ Skipping already processed video: {video_id}")
                    continue

                transcript = fetch_youtube_transcript(video_id)
                if not transcript or "Error" in transcript[0].get("text", ""):
                    print(f"⚠️ Skipping due to transcript issue: {video_id}")
                    continue

                full_text = " ".join([entry["text"] for entry in transcript])
                summary_output = summarize_final_summary_youtube(full_text)
                print(summary_output)

                new_summary = Summary(
                    title=summary_output.get("title"),
                    summary=summary_output.get("summary"),
                    source="youtube",
                    link=f"https://www.youtube.com/watch?v={video_id}",
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

                print(f"✅ Saved summary for video: {video_id}")

        session.commit()
        print("✅ All summaries stored in DB.")

    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
    finally:
        session.close()

