import os
import logging
from httpx import AsyncClient
import asyncio
import datetime
from pathlib import Path
import uuid
import base64

logger = logging.getLogger(__name__)

def filter_activity(activity_list: list[dict], keys: list[str]) -> list:
    """Filter activity list by keys"""
    return [activity for activity in activity_list if activity.get("Type", None) in keys]

def check_zh_sub(media_streams: list[dict]) -> bool:
    """Check if media_streams has chinese subtitle"""
    for stream in media_streams:
        if stream.get("Codec",None).lower() == "subrip" and stream.get("Language", None) in ["zh", "chi"]:
            display_title = stream.get("DisplayTitle", "Generic Chinese Subtitle")
            return True, display_title
    return False, "no_zh_sub"

class JellyfinAsyncClient():
    def __init__(self, url, token):
        self.url = url
        self.token = token
        self.client = AsyncClient()
        self.headers = {
            'Authorization': f'MediaBrowser Token={self.token}'
        }

    async def make_request(self, endpoint):
        """Generic API request"""
        response = await self.client.get(f'{self.url}/{endpoint}', headers=self.headers, params=None)
        return response.json()
    
    async def get_activities(self) -> set[str]: # ItemId
        """Get VideoPlaybackStopped and VideoPlayback activities"""
        endpoint = 'System/ActivityLog/Entries'
        cutoff_date = (datetime.datetime.now() - datetime.timedelta(days=3)).isoformat()
        limit = 2000
        response = await self.client.get(f'{self.url}/{endpoint}', headers=self.headers, params={'minDate':cutoff_date, 'limit':limit})
        activities = response.json().get('Items', [])
        filtered_activities = filter_activity(activities, ["VideoPlaybackStopped", "VideoPlayback"])
        return set(map(lambda x: x.get('ItemId', None), filtered_activities))
    
    async def get_item(self, item_id: str):
        """Get item data with item_id"""
        endpoint = f'Items/{item_id}'
        user_id="0a7bd095-954f-4e3b-abcc-66b9fe171db7"
        item_id = uuid.UUID(item_id).__str__()
        response = await self.client.get(f'{self.url}/{endpoint}', headers=self.headers, params={"userId": user_id})
        response = response.json()
        if response.get("Type") == "Movie":
            item_data = {
                "Name": response.get("Name", None),
                "Id": response.get("Id", None),
                "Path": response.get("Path", None),
                "OriginalTitle": response.get("OriginalTitle", None),
                "MediaStreams": response.get("MediaStreams", None),
                "ServerURL": f"{self.url}/web/#/details?id={item_id}",
                "ProviderIds": response.get("ProviderIds", []),
            }
            return item_data
        
    async def upload_subtitle(self, item_id: str, subtitle_path: str):
        with open(subtitle_path, "rb") as f:
            subtitle_data = f.read()
        encoded_subtitle = base64.b64encode(subtitle_data).decode('utf-8')
        payload = {
            "Data": encoded_subtitle,
                "Language": "chi",
                "IsForced": False,
                "Format": "srt",
                "IsHearingImpaired": False,
        }
        endpoint = f"Videos/{item_id}/Subtitles"
        response = await self.client.post(f"{self.url}/{endpoint}", headers=self.headers, json=payload)
        if response.status_code in [200,204]:
            logger.info(f"Subtitle uploaded successfully for item {item_id}.")
        else:
            logger.error(f"Failed to upload subtitle for item {item_id}. Status code: {response.status_code}")
    async def close(self):
        await self.client.aclose()
        