from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any, Optional


class NoSubtitleFound(Exception):
    """Exception raised when no subtitle is found."""
    pass

class SubtitleProvider(ABC):
    @abstractmethod
    def search_subtitle(self, **kwargs) -> List[Dict[str, Any]]:
        """Fetch subtitles from API."""
        pass
    
    @abstractmethod
    def download_subtitle(self, **kwargs) -> Optional[str]:
        """Download subtitle file."""
        pass

    @abstractmethod
    def process_downloaded_subtitle(self, **kwargs) -> Optional[str]:
        """Process downloaded subtitle file."""
        pass

    @abstractmethod
    def subtitle(self, **kwargs) -> Optional[str]:
        """Search, download and process subtitle."""
        pass