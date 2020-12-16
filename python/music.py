# music.py
# Plays Music in the /home/pi/music directory. Needs to be MP3 files

from pydub import AudioSegment
from pydub.playback import play
import os

combined = []
playlist = AudioSegment.empty()

for entry in os.scandir('/home/pi/music'):
    if entry.is_file():
        song = AudioSegment.from_mp3(entry.path)
        combined.append(song)

for song in combined:
    playlist += song

print(playlist)

play(playlist)
