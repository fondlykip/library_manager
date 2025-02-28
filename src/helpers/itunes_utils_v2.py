import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element, SubElement
import json
from datetime import datetime
from pathlib import Path
import logging
from src.config.config import COMMON_XML_PATH
from src.helpers import utils
import copy
from win32com import client as com_client
import pandas as pd
import duckdb
from typing import List


class ITunesLibrary():
    def __init__(self):
        self.media_locations = []
        self.skip_playlists = [
                                'Library',
                                'Downloaded',
                                'Music',
                                'Downloaded',
                                'Movies',
                                'Downloaded',
                                'TV Shows',
                                'Podcasts',
                                'Audiobooks',
                                'Purchased',
                                'Unplaylisted',
                                'zzzzz Dumping ground pre 2025'
                            ]
        self.itunes = com_client.Dispatch("iTunes.Application")
        self.library_tracks = None
        self.playlists = None
        self.playlist_track_mapping = None
        self.matches = None


    def get_library_dfs(self) -> List[pd.DataFrame]:
        tracks = self.itunes.LibraryPlaylist.Tracks
        count = tracks.Count
        plists = self.itunes.LibrarySource.Playlists
        p_count = plists.Count
        djp_count = plists.Count - len(self.skip_playlists)
        track_data = []
        for i in range(1, count+1):
            track = tracks.Item(i)
            try:    
                track_dict = {
                    'track_id': track.TrackDatabaseID,
                    'name': track.Name,
                    'artist': track.Artist,
                    'album': track.Album,
                    'kind': track.KindAsString,
                    'location': track.Location,
                    'track_number': track.TrackNumber,
                    'total_time': track.Time,
                }
                track_data.append(track_dict)
            except:
                continue
        self.library_tracks = pd.DataFrame(track_data)
        print("library tracks created")

        plist_mappings = []
        playlist_data = []
        for i in range(1, p_count+1):
            playlist = plists.Item(i)
            plist_id = playlist.playlistID
            playlist_dict = {
                'playlist_id': plist_id,
                'name': playlist.Name
            }
            playlist_data.append(playlist_dict)
            plist_tracks = playlist.Tracks
            pltrack_count = plist_tracks.Count
            for i in range(1, pltrack_count+1):
                plist_track = plist_tracks.Item(i)
                plist_mapping = {
                    'playlist_id': plist_id,
                    'plist_name': playlist.Name,
                    'track_id': plist_track.TrackDatabaseID,
                    'track_name': plist_track.Name
                }
                plist_mappings.append(plist_mapping)

        self.playlists = pd.DataFrame(playlist_data)
        self.playlist_track_mapping = pd.DataFrame(plist_mappings)
        print("playlist and track mapping created")
        return True


    def run_matching(self):
            library_tracks = self.library_tracks
            playlists = self.playlists
            playlist_track_mapping = self.playlist_track_mapping
            with open('./src/sql/matching_ddb.sql', 'r') as f:
                query = f.read()
            #print(query)
            self.matches = duckdb.query(query).to_df()
            return len(self.matches.index)


    def export_csvs(self, output_path: Path):
        file_timestamp = datetime.now().strftime("%Y%m%d%H%M")
        export_list = [
            (k, var)\
             for k, var in self.__dict__.items()\
             if type(var) == type(pd.DataFrame())
        ]
        for key, df in export_list:
            if df.shape[0] > 0:
                file_name = f'{key}-{file_timestamp}.csv'
                print(f"save {key} to {file_name}")
                df.to_csv(f"./{file_name}", index=False)


    def get_media_locations(self):
        tracks = self.itunes.LibrarySource.Tracks
        print(tracks.Count)

    def replace_matches(self):
        for idx, match in self.matches.iterrows():
            print(f"playlist ID: {match['playlist_id']}")
            plist = self.itunes.GetITObjectByID(None,
                                                match['playlist_id'],
                                                None, None)
            new_track = self.itunes.GetITObjectByID(None, None, None,
                                                    match['aif_id'])
            print(f"name: {plist.Name}")
            print(f"new track: {new_track.Name}")

            #       plist = self.itunes.GetITObjectByID(None,
            #       File "<COMObject iTunes.Application>", line 2, in GetITObjectByID
            #       TypeError: int() argument must be a string, a bytes-like object or a number, not 'NoneType'