import json
import time
from datetime import datetime, timezone
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

API_KEY = "AIzaSyCrWk-Ot8uOxQl2_scAhkE3rkqOi9PAXnY"

CHANNEL_IDS = [
    "UUYj1jy66peKPzEp808TK5ww",
    "UURJBeQUrU5YPGlchWkva5xw",
    "UULR63YCHMfBp4i9zyC6DU3g",
    "UUBSMDyh_5qG8grvVu-VIEuw",
]

START_DATE = "2025-01-01T00:00:00Z" 
END_DATE = "2026-08-31T23:59:59Z" 

OUTPUT_FILENAME = "DADOS_COMENTARIOS.json"

def get_youtube_client(api_key):
    return build("youtube", "v3", developerKey=api_key)

def parse_iso_date(date_str):
    return datetime.fromisoformat(date_str.replace("Z", "+00:00"))

def get_videos_in_timerange(youtube, channel_id, start_date_str, end_date_str):
    videos = []
    next_page_token = None

    start_dt = parse_iso_date(start_date_str)
    end_dt = parse_iso_date(end_date_str)

    uploads_playlist_id = "UU" + channel_id[2:] if channel_id.startswith("UC") else channel_id

    print(f"\n--> Buscando playlist de envios: {uploads_playlist_id}")

    while True:
        try:
            request = youtube.playlistItems().list(
                part="snippet", 
                playlistId=uploads_playlist_id,
                maxResults=50,
                pageToken=next_page_token,
            )
            response = request.execute()

            for item in response.get("items", []):
                snippet = item["snippet"]

                published_at_str = snippet.get("publishedAt")
                if not published_at_str:
                    continue

                published_dt = parse_iso_date(published_at_str) 

                if start_dt <= published_dt <= end_dt:
                    video_id = snippet["resourceId"]["videoId"]
                    title = snippet["title"]  

                    videos.append(
                        {
                            "video_id": video_id,
                            "title": title,
                            "published_at": published_at_str,
                        }
                    )

                elif published_dt < start_dt:
                    print(f"    Alcançado video anterior a {start_date_str}. Interrompendo busca no canal.")
                    return videos

            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break        
    
        except Exception as e:
            print(f" [Erro] Falha ao listar videos da playlist: {e}")
            break

    print(f"    Encontrados {len(videos)} videos no periodo selecionado")
    return videos

def get_video_comments(youtube, video_id):
    comments = []
    next_page_token = None

    while True:
        try:
            request = youtube.commentThreads().list(
                part="snippet,replies",
                videoId=video_id,
                maxResults=100,
                textFormat="plainText",
                pageToken=next_page_token, 
            )
            response = request.execute()

            for item in response.get("items", []):
                top_comment = item["snippet"]["topLevelComment"]["snippet"]

                author_channel_id = top_comment.get("authorChannelId", {}).get("value", "ANONYMOUS")
                
                comment_data = {
                    "comment_id": item["id"],
                    "author_id": author_channel_id,
                    "author_name": top_comment.get("authorDisplayName"),
                    "text": top_comment.get("textDisplay"),
                    "like_count": top_comment.get("likeCount", 0),
                    "published_at": top_comment.get("publishedAt"),
                    "is_reply": False,          
                }
                comments.append(comment_data)

                if "replies" in item:
                    for reply_item in item["replies"]["comments"]:
                        reply_snippet = reply_item["snippet"]
                        
                        reply_author_id = reply_snippet.get("authorChannelId", {}).get("value", "ANONYMOUS")
                        
                        comments.append(
                            {
                                "comment_id": reply_item["id"],
                                "author_id": reply_author_id,
                                "author_name": reply_snippet.get("authorDisplayName"),
                                "text": reply_snippet.get("textDisplay"),
                                "like_count": reply_snippet.get("likeCount", 0),
                                "published_at": reply_snippet.get("publishedAt"),
                                "is_reply": True,
                                "parent_id": item["id"],
                            }
                        )
            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break
        except HttpError as e:
            if "commentsDisabled" in str(e):
                print(f"     [Aviso] comentários desativados para o video {video_id}.")
            else:
                print(f"     [Erro] Falha ao extrair comentario do video {video_id}: {e}")
            break

    return comments

def main():
    youtube = get_youtube_client(API_KEY)
    dataset = {
        "metadata": {
            "extracted_at": datetime.now(timezone.utc).isoformat(),
            "time_window": {"start": START_DATE, "end": END_DATE},
            "total_channels": len(CHANNEL_IDS),
        },
        "channels": [],
    }
    
    total_comments_extracted = 0

    for channel_id in CHANNEL_IDS:
        videos = get_videos_in_timerange(youtube, channel_id, START_DATE, END_DATE)
        channel_data = {
            "channel_id": channel_id,
            "total_videos": len(videos),
            "videos": [],
        }

        for idx, video in enumerate(videos, 1):
            print(f"  -> Extraindo comentarios [{idx}/{len(videos)}]: {video['title']} ({video['video_id']})")
            comments = get_video_comments(youtube, video["video_id"])
            video["comments_count"] = len(comments)
            video["comments"] = comments

            channel_data["videos"].append(video)
            total_comments_extracted += len(comments)

            time.sleep(0.1)

        dataset["channels"].append(channel_data)
        
    dataset["metadata"]["total_comments"] = total_comments_extracted

    with open(OUTPUT_FILENAME, 'w', encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 45)
    print(" Extração concluída com sucesso")
    print(f" Total de comentários coletados: {total_comments_extracted}")
    print(f" Arquivo gerado: {OUTPUT_FILENAME}")
    print("=" * 45) 

if __name__ == "__main__":
    main()