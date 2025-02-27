from pathlib import Path
import re

def parse_bandcamp_song(file_name: str):
    file_name, extension = file_name.split('.')
    file_name_splits = file_name.split(' - ')
    file_meta = {
        'artist': None,
        'album': None,
        'track': None,
        'title': None
    }

    if len(file_name_splits) == 1:
        file_meta['title'] = file_name_splits[0]
        return file_meta

    if len(file_name_splits) == 2:
        # 'artist - song_name'
        file_meta['artist'] = file_name_splits[0]
        file_meta['title'] = file_name_splits[1]
        return file_meta

    elif len(file_name_splits) == 3:
        # \artist - album - song.aiff
        artist = file_name_splits[0]
        album = file_name_splits[1]
        track_title = file_name_splits[2]
        title = track_title[3:]
        track = track_title[:2]
        file_meta['artist'] = artist
        file_meta['album'] = album
        file_meta['title'] = title
        file_meta['track'] = track
        return file_meta

    elif len(file_name_splits) > 3:
        track_title_arr = []
        rest = []
        found_start = False
        for split in file_name_splits:
            if re.match("^\d{2}", split):
                found_start = True

            if found_start:
                track_title_arr.append(split)
            else:
                rest.append(split)

        if len(track_title_arr) == 1:
            title = track_title_arr[0][3:]
            track = track_title_arr[0][:2]

        elif len(track_title_arr) > 1:
            artist = track_title_arr[0][3:]
            track  = track_title_arr[0][:2]
            title = ' - '.join(track_title_arr[1:])

        if not artist:
            artist = rest[0]
        album = ' - '.join(rest[1:])
        file_meta['artist'] = artist
        file_meta['album'] = album
        file_meta['title'] = title
        file_meta['track'] = track
        return file_meta

    else:
        print(f"Unknown number of splits: {len(file_name_splits)}")
        return False


def get_album_artist_from_name(filename: str):
    """
    Split the album artist and track name from hyphen
    delimited filename
    """
    album, artist, name = '', '', ''
    splits = filename.split(' - ')
    if len(splits) > 3:
        artist = splits[:1]
        find_album = True
        album_parts = []
        name_parts = []
        for split in splits[1:]:
            if re.match(r'\d{2}', split):
                find_album = False
            if find_album:
                album_parts.append(split)
            else:
                name_parts.append(split)
        album = ' - '.join(album_parts)
        name = ' - '.join(name_parts)
    elif len(splits) == 3:
        artist, album, name = splits
    elif len(splits) == 3:
        artist, name = splits
        album = None
    else:
        album = None
        artist = None
        name = filename
    return album, artist, name