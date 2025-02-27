import re
import os
import mutagen
from pathlib import Path
from mutagen.wave import WAVE
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TRCK
from mutagen.easyid3 import EasyID3
from mutagen.aiff import AIFF



def update_tags(audio, artist, album, track, title, total_tracks):
    # if title:
    #     audio["TIT2"] = TIT2(text=title)  # Title
    # if artist:
    #     audio["TPE1"] = TPE1(text = [artist])  # Artist
    # if album:
    #     audio["TALB"] = TALB(text = [str(album)]) 
    # if track:
    #     if not total_tracks:
    #         total_tracks = track    
    #     audio["TRCK"] = TRCK(text = [(int(track), int(total_tracks))]) 
    pass

def get_tags(file: Path):
    if not isinstance(file, Path):
        print(f"file must be a path")
        return False

    if not file.is_file() and not file.name.endswith('aiff'):
        print("path must be to a valid file")
    
    try:
        audio = AIFF(file.absolute())
        
        # Load ID3 tags
        if audio.tags is not None:
            dtags = {
                'artist': audio['TPE1'],
                'album': audio['TALB'],
                'title': audio['TIT2'],
                'track': audio['TRCK']
                }
            return dtags
        else:
            print("No ID3 tags found.")
            return False

    except Exception as e:
        print(f"Error reading AIFF file: {e}")
