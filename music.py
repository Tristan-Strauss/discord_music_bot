import asyncio
import yt_dlp
import discord

from config import YDL_OPTIONS, FFMPEG_OPTIONS
from utils import now_playing_text

song_queue = []
song_history = []
current_song = None


async def play_youtube_audio(client, voice_client, song_data, text_channel):
    global current_song

    current_song = song_data
    song_history.append(song_data)

    url = song_data["url"]
    title = song_data["title"]

    loop = asyncio.get_running_loop()

    def extract():
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            return ydl.extract_info(url, download=False)

    info = await loop.run_in_executor(None, extract)
    audio_url = info["url"]

    source = discord.FFmpegPCMAudio(audio_url, **FFMPEG_OPTIONS)

    def after_playing(error):
        if error:
            print(error)

        asyncio.run_coroutine_threadsafe(
            play_next_song(client, voice_client, text_channel),
            client.loop
        )

    voice_client.play(source, after=after_playing)

    await text_channel.send(
        now_playing_text(title, song_queue, song_history)
    )


async def play_next_song(client, voice_client, text_channel):
    if len(song_queue) == 0:
        return

    next_song = song_queue.pop(0)

    await play_youtube_audio(
        client,
        voice_client,
        next_song,
        text_channel
    )