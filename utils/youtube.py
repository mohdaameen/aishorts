import os
import json
import requests
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi
from datetime import datetime
from .summarizer import summarize_final_summary
from models.schemas import UserCredential, VideoSummaryGlobal, UserVideoMap, UserPreference
from sqlalchemy.exc import IntegrityError

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")



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
    print(f"🕒 process_all_users() triggered at {datetime.now()}")
    session = db.get_session()

    try:
        users = session.query(UserCredential).all()
        all_keywords = set()
        keyword_user_map = {}

        for user in users:
            for pref in user.preferences:
                keyword = pref.keyword.lower()
                all_keywords.add(keyword)
                keyword_user_map.setdefault(keyword, set()).add(user.id)

        for channel_id in PREDEFINED_CHANNELS:
            print(f"\n📺 Checking channel: {channel_id}")
            videos = get_latest_videos_from_channel(channel_id)

            for video in videos:
                video_id = video["video_id"]
                title = video["title"]
                description = video["description"]

                already_processed = session.query(VideoSummary).filter_by(video_id=video_id).first()
                if already_processed:
                    print(f"✅ Skipping already processed video globally: {video_id}")
                    continue

                matched_keywords = [kw for kw in all_keywords if kw in f"{title} {description}".lower()]
                if not matched_keywords:
                    continue

                transcript = fetch_youtube_transcript(video_id)
                if not transcript or "Error" in transcript[0].get("text", ""):
                    continue

                full_text = " ".join([entry["text"] for entry in transcript])
                summary = summarize_final_summary(full_text)

                summary_data = {
                    "video_id": video_id,
                    "video_title": summary.get("title"),
                    "video_link": f"https://www.youtube.com/watch?v={video_id}",
                    "summary": summary.get("summary"),
                    "tags": summary.get("tags"),
                    "category": summary.get("category"),
                    "source": "youtube"
                }

                processed_users = set()

                for keyword in matched_keywords:
                    for user_id in keyword_user_map[keyword]:
                        if user_id in processed_users:
                            continue

                        session.add(VideoSummary(user_id=user_id, **summary_data))
                        processed_users.add(user_id)

        session.commit()
        print("✅ All summaries stored in DB.")
    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
    finally:
        session.close()
