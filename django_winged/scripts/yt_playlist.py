import re
import datetime
from googleapiclient.discovery import build
from django.contrib.auth.models import User
from winged_app.models import Container, Item

def run():
    api_key = 'AIzaSyDMjbEw3Htx3bD151hqMCjuggNusOrRYz0'
    playlist_link = 'https://youtube.com/playlist?list=PLCNqLM5E_QAhDFVHwNe2ZXH7Q5f7YZSr4'  # Replace with the link to the playlist you want to retrieve

    # Extract the playlist ID from the playlist link
    playlist_id = re.search(r'(?<=list=)[\w-]+', playlist_link).group(0)

    # Retrieve the videos in the playlist using the YouTube Data API.
    with build('youtube', 'v3', developerKey=api_key) as youtube:
        videos = []
        next_page_token = None
        while True:
            playlist_items_request = youtube.playlistItems().list(
                part='snippet,contentDetails',
                playlistId=playlist_id,
                maxResults=50,
                pageToken=next_page_token
            )
            playlist_items_response = playlist_items_request.execute()

            for item in playlist_items_response['items']:
                video_channel = item['snippet']['videoOwnerChannelTitle']
                video_title = item['snippet']['title']
                
                videos.append(video_channel + ": " + video_title)

            next_page_token = playlist_items_response.get('nextPageToken')
            if not next_page_token:
                break


# Create a container with the name of the playlist
    container_name = re.search(r'(?<=list=)[^&]+', playlist_link).group(0)

    container = Container.objects.create(name=container_name, user=User.objects.first())

    # Add all videos as actionable items to the container
    for video in videos:
        print(video)
        item = Item.objects.create(
            statement=video,
            actionable=True,
            parent_container=container,
            user=User.objects.first(),
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now()
        )