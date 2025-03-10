import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element, SubElement
import json
from datetime import datetime
from pathlib import Path
import logging
from config.config import COMMON_XML_PATH
from helpers import utils
import copy
from win32com import client as com_client
import pandas as pd
import duckdb
from typing import List


class ITunesLibrary():
    def __init__(self, library_xml_loc: str = "C:\\Users\\liamj\\Music\\iTunes\\iTunes Music Library.xml"):
        self.library_xml_loc = Path(library_xml_loc)
        self.library_data_path = Path("C:\\Users\\liamj\\Music\\iTunes")
        self.library_dict = self.parse_xml(self.library_xml_loc)
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
        self.library_tracks = pd.DataFrame
        self.lt_cols = self.library_tracks.columns.to_list()
        self.playlists = pd.DataFrame
        self.pl_cols = self.playlists.columns.to_list()
        self.playlist_track_mapping = pd.DataFrame
        self.ptm_cols = self.playlist_track_mapping.columns.to_list()
        self.matches = pd.DataFrame


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
                    'track_id': track.trackID,
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
        self.lt_cols = list(self.library_tracks.columns())

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
                    'track_id': plist_track.trackID
                }
                plist_mappings.append(plist_mapping)

        self.playlists = pd.DataFrame(playlist_data)
        self.pl_cols = list(self.playlists.columns)

        self.playlist_track_mapping = pd.DataFrame(plist_mappings)
        self.ptm_cols = list(self.playlist_track_mapping.columns())
        return True


    def run_matching(self):
            library_tracks = self.library_tracks
            playlists = self.playlists
            playlist_track_mapping = self.playlist_track_mapping
            with open('./matching_sql.sql', 'r') as f:
                query = f.read()
            clean_query = query.replace("itunes.", "")
            print(clean_query)
            self.matches = duckdb.query(clean_query).to_df()
            return len(self.matches.index)


    def export_csvs(self, output_path: Path):
        file_timestamp = datetime.now().strftime("%Y%m%d%H%M")
        export_list = [
            self.library_tracks, self.playlists, self.playlist_track_mapping,
            self.
        ]
        self.library_tracks.to_csv(Path / f'library_tracks-{file_timestamp}.csv')
