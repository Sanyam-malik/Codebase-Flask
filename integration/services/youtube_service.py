import logging
from googleapiclient.discovery import build
from config_manager import config_manager as appenv


def is_available():
    # Check if the YOUTUBE_API_KEY is present in the environment variables
    return appenv.environ['YOUTUBE_API_KEY'] is not None


def get_top_youtube_videos(query):
    try:
        youtube = build('youtube', 'v3', developerKey=appenv.environ['YOUTUBE_API_KEY'])

        # Search for the query
        search_response = youtube.search().list(
            q=query,
            part='snippet',
            maxResults=25,  # Retrieve 25 results to ensure we have enough to filter by views
            type='video',
            order='relevance'
        ).execute()

        # Extract video IDs
        video_ids = [item['id']['videoId'] for item in search_response['items']]

        # Get video statistics
        video_response = youtube.videos().list(
            id=','.join(video_ids),
            part='snippet,statistics'
        ).execute()

        # Sort videos by view count
        videos = video_response['items']

        # Return video details
        return {
            "message": "success",
            "content": [{
                'title': video['snippet']['title'],
                'description': video['snippet']['description'],
                'channelTitle': video['snippet']['channelTitle'],
                'viewCount': video['statistics']['viewCount'],
                'videoId': video['id'],
                'url': f"https://www.youtube.com/watch?v={video['id']}",
                'thumbnail': video['snippet']['thumbnails']['high']['url']  # Get high resolution thumbnail
            } for video in videos]
        }
    except Exception as e:
        logging.info(f"Error while calling youtube api....\n{e}")
        return {
            "message": "error"
        }
