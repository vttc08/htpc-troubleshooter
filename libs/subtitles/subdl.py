import zipfile
import httpx
import os
from typing import List, Dict, Any, Optional
from .base import SubtitleProvider, NoSubtitleFound
from libs.configuration import subdl_api_key

class SubDLProvider(SubtitleProvider):
    def __init__(self):
        self.api_url = "https://api.subdl.com/api/v1/subtitles"
        self.dl_url = "https://dl.subdl.com"
        self.api_key = subdl_api_key
        self.languages = "ZH"

    def search_subtitle(self, **kwargs) -> List[Dict[str, Any]]:
        """Fetch subtitles using SubDL API."""
        # Placeholder for actual implementation
        tmdb_id = kwargs.get("tmdb_id")
        print(f"Searching subtitles for TMDB ID: {tmdb_id}")
        print(f"Using API URL: {self.api_url}")
        print(f"Using API Key: {self.api_key}")
        with httpx.Client() as client:
            response = client.get(self.api_url, params={
                "tmdb_id": tmdb_id,
                "api_key": self.api_key,
                "languages": self.languages
            })
            if response.status_code == 200:
                if len(response.json().get("subtitles", [])) == 0:
                    raise NoSubtitleFound("No subtitles found for the given TMDB ID.")
                return response.json()
            else:
                print(f"Error: {response.status_code} - {response.text}")
                return []

    def download_subtitle(self, url) -> Optional[str]:
        filename = url.split("/")[-1]
        self.file_path = f"./libs/tmp/{filename}"
        with httpx.Client() as client:
            response = client.get(url)
            if response.status_code == 200:
                with open(self.file_path, "wb") as f:
                    f.write(response.content)
                return self.file_path
            else:
                print(f"Error: {response.status_code} - {response.text}")
                return None
            
    def process_downloaded_subtitle(self, **kwargs) -> Optional[str]:
        """Process the downloaded subtitle file."""
        # Placeholder for actual implementation
        if self.file_path.endswith(".zip"):
            self.extracted_dir = self.file_path.replace(".zip", "")
            with zipfile.ZipFile(self.file_path, 'r') as zip_ref:
                zip_ref.extractall(self.extracted_dir)
            self.srtfile = os.path.join(self.extracted_dir, os.listdir(self.extracted_dir)[0])
        elif self.file_path.endswith(".srt"):
            self.srtfile = self.file_path
        with open(self.srtfile, "r", encoding="utf-8") as f:
            content = f.read()
        return self.srtfile

    def subtitle(self, **kwargs) -> Optional[str]:
        """Search, download and process subtitle."""
        tmdb_id = kwargs.get("tmdb_id")
        subtitles = self.search_subtitle(tmdb_id=tmdb_id)
        subtitle_url = f"{self.dl_url}{subtitles.get('subtitles')[0]['url']}"
        self.download_subtitle(url=subtitle_url)
        print(self.process_downloaded_subtitle())
        return self.process_downloaded_subtitle()