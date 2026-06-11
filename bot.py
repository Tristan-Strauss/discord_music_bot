import asyncio
import yt_dlp
import discord

from config import YDL_OPTIONS
from utils import is_youtube_url, send_help
from music import (
    song_queue,
    song_history,
    current_song,
    play_youtube_audio,
    play_next_song
)

intents=discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


async def join_voice_channel_from_message(message):
    if not (message.author.voice and message.author.voice.channel):
        await message.channel.send("Join a voice channel first.")
        return None
    channel = message.author.voice.channel
    if message.guild.voice_client:
        await message.guild.voice_client.move_to(channel)
        return message.guild.voice_client
    return await channel.connect()


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")


@client.event
async def on_message(message):
    global current_song
    if message.author == client.user:
        return
    content = message.content

    # ---------------- PING ----------------
    if content.startswith("$ping"):
        await message.channel.send("Pong!")

    # ---------------- JOIN ----------------
    elif content.startswith("$join"):
        await join_voice_channel_from_message(message)

    # ---------------- LEAVE ----------------
    elif content.startswith("$leave"):
        vc = message.guild.voice_client
        if vc:
            song_queue.clear()
            song_history.clear()
            await vc.disconnect()

    # ---------------- HELP ----------------
    elif content.startswith("$help"):
        await send_help(message.channel)

    # ---------------- PLAY ----------------
    elif content.startswith("$play"):
        parts = content.split(" ", 1)
        if len(parts) < 2:
            await message.channel.send("Usage: `$play <youtube_url or search term>`")
            return
        query = parts[1].strip()
        voice_client = await join_voice_channel_from_message(message)
        if voice_client is None:
            return
        # URL MODE
        if is_youtube_url(query):
            url = query
        else:
            await message.channel.send(f"🔎 Searching YouTube for: **{query}**")
            loop = asyncio.get_running_loop()
            def search():
                with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                    return ydl.extract_info(f"ytsearch1:{query}", download=False)
            info = await loop.run_in_executor(None, search)
            if not info or not info.get("entries"):
                await message.channel.send("❌ No results found.")
                return
            url = info["entries"][0]["webpage_url"]
        # FETCH METADATA
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=False)
        song_data = {
            "url": url,
            "title": info.get("title", "Unknown")
        }
        # QUEUE LOGIC
        if voice_client.is_playing() or voice_client.is_paused():
            song_queue.append(song_data)
            await message.channel.send(f"➕ Added to queue: **{song_data['title']}**")
        else:
            await play_youtube_audio(
                client,
                voice_client,
                song_data,
                message.channel
            )

    # ---------------- NEXT ----------------
    elif content.startswith("$next"):
        vc = message.guild.voice_client
        if vc:
            play_next_song(client, vc, message.channel)
    # ---------------- STOP ----------------
    elif content.startswith("$stop"):
        vc = message.guild.voice_client
        if vc:
            song_queue.clear()
            song_history.clear()
            vc.stop()
            await vc.disconnect()
            await message.channel.send("⏹ Stopped and disconnected.")

    # ---------------- QUEUE ----------------
    elif content.startswith("$queue"):
        if not song_queue:
            await message.channel.send("📋 Queue is empty.")
            return
        queue_text = "\n".join(
            f"{i+1}. {s['title']} - {s['url']}"
            for i, s in enumerate(song_queue)
        )
        await message.channel.send(f"📋 **Queue:**\n{queue_text}")
