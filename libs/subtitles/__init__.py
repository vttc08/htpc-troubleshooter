from .base import SubtitleProvider
from .subdl import SubDLProvider, NoSubtitleFound

# List of providers we can try
subtitle_providers = [
    SubDLProvider(),
]
