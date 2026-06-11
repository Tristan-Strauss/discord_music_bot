import os
from dotenv import load_dotenv

load_dotenv(override=True)

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

YDL_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
}

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}