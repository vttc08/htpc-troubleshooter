import json
import sys
import asyncio

from ffmpeg.asyncio import FFmpeg
from ffmpeg.errors import FFmpegFileNotFound
import re
from dataclasses import dataclass, field
from libs.configuration import ffm_debug
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# pip install python-ffmpeg
"\\10.10.120.16\movies_share\21 Bridges (2019)"
"/mnt/data/Movies/21 Bridges (2019)/"
"\\10.10.120.16\movies_2_share\21 Bridges (2019)"
"/mnt/data2/Movies/21 Bridges (2019)/"


    
@dataclass(order=False)
class AudioCodec:
    sort_index: int = field(init=False, repr=False)
    raw_data: str
    is_atmos: bool
    
    def __post_init__(self):
        self.raw_data: str = self.raw_data.lower()
        if "atmos" in self.raw_data:
            self.is_atmos = True
        if re.search(" - |\/", self.raw_data):  # if receiver input
            self.raw_data = re.split(" - |\/", self.raw_data)[1]
        mapping = {
            "ac3": {"aliases": ["ac3", "dd", "dolby digital"], "score": 10},
            "eac3": {"aliases": ["eac3", "ddp", "dd+"], "score": 20},
            "truehd": {"aliases": ["truehd", "dolby truehd"], "score": 50},
            "pcm": {"aliases": ["pcm", "lpcm"], "score": -99999},
            "dts": {"aliases": ["dts", "dts-hd ma", "dtshd-ma"], "score": 60}, # Not implemented yet
        }
        map_dict = {alias: key for key, value in mapping.items() for alias in value['aliases']}
        self.ac = map_dict.get(self.raw_data, "dts")
        self.score = mapping.get(self.ac, {"score": 0})['score']
        if self.is_atmos:
            self.score += 10
        self.sort_index = self.score
    def __lt__(self, other):
        if not isinstance(other, AudioCodec):
            return NotImplemented
        return self.sort_index < other.sort_index
        
def path_replacement(path: str) -> str:
    """Replace server path with temp SMB path to debug on Windows"""
    if ffm_debug == "1": # 1 or 0, dotenv do not support boolean
        paths = path.split("/")
        paths[0] = "/"
        share_link = f"{paths[3].lower()}_{f'{paths[2][-1]}_' if paths[2][-1].isdigit() else ''}share"
        paths[1:4] = ["10.10.120.16", share_link]
        path = "/".join(paths)
        return path
    else:
        return path
    
async def probe(path) -> tuple[AudioCodec, bool, bool]:
    path = path_replacement(path)
    try:
        ffprobe = FFmpeg(executable="ffprobe").input(
            path,
            print_format="json", # ffprobe will output the results in JSON format
            show_streams=None,
        )
    except FFmpegFileNotFound:
        logger.error(f"FFprobe will assume generic results that is not the actual media because it encountered an error with location, {path}.")
        return AudioCodec("pcm", False), False, False
        

    media = json.loads(await ffprobe.execute())
    ms: dict= media['streams']
    video: int = next((index for (index, d) in enumerate(ms) if d['codec_type'] == 'video'), None)
    audios: list = [index for (index, d) in enumerate(ms) if d['codec_type'] == 'audio']
    dvp = ms[video].get("side_data_list", None)
    dvp = dvp[0].get("dv_profile", None) if dvp else None
    codecs = []
    for audio in audios:
        ac = str(ms[audio].get("codec_name", None)).lower()
        if ac == 'dts':
            ac = "dtshd-ma" if "dts-hd ma" in ms[audio].get("profile", None) else "dts"
        is_atmos = True if "atmos" in str(ms[audio].get("profile", None)).lower() else False
        codecs.append(AudioCodec(ac, is_atmos))
    is_p7 = True if dvp == 7 else False
    src_codec = max(codecs)
    return src_codec, is_p7, is_atmos

# Dolby Vision Compatibilty ID
# P5 = 0
# P7 = 6
# P8 = 1