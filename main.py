from dotenv import load_dotenv
import os
import asyncio
import discord
import yt_dlp

load_dotenv(override=True)
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

YDL_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
}

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}

# -----------------------------
# GLOBAL STATE
# -----------------------------
song_queue = []
song_history = []
current_song = None


# -----------------------------
# HELP
# -----------------------------
async def send_help(message):
    help_text = """
🎵 **Music Bot Commands**

`$play <youtube_url>` → Play or queue a song  
`$next` → Skip song  
`$previous` → Go back  
`$stop` → Stop and disconnect  
`$queue` → Show queue  
`$ping` → Check bot  
`$help` → Show help
"""
    await message.channel.send(help_text)


def now_playing_text(title):
    if len(song_queue) == 0:
        return f"🎵 **Now Playing:** {title}\n📋 Queue: empty"

    return (
        f"🎵 **Now Playing:** {title}\n"
        f"📋 Queue size: {len(song_queue)} song(s)\n"
        f"▶️ In session: #{len(song_history)}"
    )


# -----------------------------
# EVENTS
# -----------------------------
@client.event
async def on_ready():
    print(f"Logged in as {client.user}")


@client.event
async def on_message(message):
    global current_song

    if message.author == client.user:
        return

    # ---------------- PING ----------------
    if message.content.startswith("$ping"):
        await message.channel.send("Pong!")

    # ---------------- HELP ----------------
    elif message.content.startswith("$help"):
        await send_help(message)

    # ---------------- PLAY ----------------
    elif message.content.startswith("$play"):
        try:
            url = message.content.split(" ", 1)[1]
        except IndexError:
            await message.channel.send("Usage: `$play <youtube_url>`")
            return

        voice_client = await join_voice_channel_from_message(message)
        if voice_client is None:
            return

        # Extract video info
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=False)

        title = info.get("title", "Unknown")

        song_data = {
            "url": url,
            "title": title
        }

        if voice_client.is_playing() or voice_client.is_paused():
            song_queue.append(song_data)
            await message.channel.send(
                f"➕ Added to queue: {title} (#{len(song_queue)})"
            )
        else:
            await play_youtube_audio(
                voice_client,
                song_data,
                message.channel
            )

    # ---------------- NEXT ----------------
    elif message.content.startswith("$next"):
        voice_client = message.guild.voice_client
        if voice_client:
            voice_client.stop()

    # ---------------- PREVIOUS ----------------
    elif message.content.startswith("$previous"):
        voice_client = message.guild.voice_client

        if len(song_history) < 2:
            await message.channel.send("No previous song available.")
            return

        if current_song:
            song_queue.insert(0, current_song)

        song_history.pop()
        previous_song = song_history.pop()

        if voice_client:
            voice_client.stop()

        await play_youtube_audio(
            voice_client,
            previous_song,
            message.channel
        )

    # ---------------- STOP ----------------
    elif message.content.startswith("$stop"):
        voice_client = message.guild.voice_client

        if voice_client:
            song_queue.clear()
            song_history.clear()
            current_song = None

            voice_client.stop()
            await voice_client.disconnect()

            await message.channel.send("⏹ Stopped and disconnected.")

    # ---------------- QUEUE ----------------
    elif message.content.startswith("$queue"):
        if len(song_queue) == 0:
            await message.channel.send("📋 Queue is empty.")
            return

        queue_text = "\n".join(
            [
                f"{i+1}. {song['title']} - {song['url']}"
                for i, song in enumerate(song_queue)
            ]
        )

        await message.channel.send(f"📋 **Queue:**\n{queue_text}")


# -----------------------------
# VOICE JOIN
# -----------------------------
async def join_voice_channel_from_message(message):
    if not (message.author.voice and message.author.voice.channel):
        await message.channel.send("Join a voice channel first.")
        return None

    channel = message.author.voice.channel

    if message.guild.voice_client:
        await message.guild.voice_client.move_to(channel)
        return message.guild.voice_client

    return await channel.connect()


# -----------------------------
# PLAY SONG
# -----------------------------
async def play_youtube_audio(voice_client, song_data, text_channel):
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

    source = discord.FFmpegPCMAudio(
        audio_url,
        **FFMPEG_OPTIONS
    )

    def after_playing(error):
        if error:
            print(error)

        asyncio.run_coroutine_threadsafe(
            play_next_song(voice_client, text_channel),
            client.loop
        )

    voice_client.play(source, after=after_playing)

    await text_channel.send(
        now_playing_text(title)
    )


# -----------------------------
# NEXT SONG
# -----------------------------
async def play_next_song(voice_client, text_channel):
    if len(song_queue) == 0:
        return

    next_song = song_queue.pop(0)

    await play_youtube_audio(
        voice_client,
        next_song,
        text_channel
    )


# -----------------------------
# RUN BOT
# -----------------------------
if __name__ == "__main__":
    client.run(DISCORD_TOKEN)