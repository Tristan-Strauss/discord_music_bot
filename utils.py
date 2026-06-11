import re

def is_youtube_url(url: str) -> bool:
    youtube_regex = re.compile(
        r"(https?://)?(www\.)?(youtube\.com|youtu\.be|music\.youtube\.com)/.+"
    )
    return bool(youtube_regex.match(url))


def now_playing_text(title, song_queue, song_history):
    if len(song_queue) == 0:
        return f"🎵 **Now Playing:** {title}\n📋 Queue: empty"

    return (
        f"🎵 **Now Playing:** {title}\n"
        f"📋 Queue size: {len(song_queue)} song(s)\n"
        f"▶️ In session: #{len(song_history)}"
    )


async def send_help(channel):
    help_text = """
🎵 **Music Bot Commands**

`$play <youtube_url or search term>`
• Play a YouTube video or search for a song.

`$next`
• Skip to the next song.

`$previous`
• Go back to previous song.

`$queue`
• Show current queue.

`$stop`
• Stop playback and disconnect.

`$ping`
• Check bot status.

`$help`
• Show this help.
"""
    await channel.send(help_text)