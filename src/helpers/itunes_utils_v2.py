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
                    'track_id': track.trackID,
                    'name': track.Name,
                    'artist': track.Artist,
                    'album': track.Album,
                    'kind': track.KindAsString,
                    'location': track.Location,
                    'track_number': track.TrackNumber,
                    'total_time': track.Time,
                    'source_id': track.sourceID,
                    'playlist_id': track.playlistID,
                    'track_database_id': track.TrackDatabaseID

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
                    'track_id': plist_track.trackID,
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
            # include the various object IDs in the data
            #       plist = self.itunes.GetITObjectByID(None,
            #       File "<COMObject iTunes.Application>", line 2, in GetITObjectByID
            #       TypeError: int() argument must be a string, a bytes-like object or a number, not 'NoneType'

    def test_playlist_operations(self):
        playlists = self.itunes.LibrarySource.Playlists
        p_count = playlists.Count
        for i in range(1, p_count+1):
            if playlists.Item(i).Name == 'test_playlist':
                print(i)
                print(playlists.Item(i).Name)
                test_playlist = playlists.Item(i)
                print(test_playlist.Tracks.Count)
                tp_pids = self.itunes.GetITObjectPersistentIDs(test_playlist)
                print(tp_pids)
        print('Library Tracks')
        library_tracks = self.itunes.LibraryPlaylist.Tracks
        lt_count = library_tracks.Count
        at_oids = []
        for i in range(1, lt_count+1):
            track = library_tracks.Item(i)
            if track.Name == 'SUSMAN=V2':
                t_oid = track.GetITObjectIDs()
                kind = track.KindAsString
                if kind == 'AIFF audio file':
                    added_track = test_playlist.AddTrack(track)
                    at_oid = added_track.GetITObjectIDs()
                    at_oids.append(at_oid)
                    print(f"Track added, {test_playlist.Tracks.Count}")

                    print("Add Track to test playlist", added_track.Name, added_track.GetITObjectIDs(), added_track.KindAsString, added_track.Playlist.Name, at_oid, t_oid)
        print(tp_pids)
        print(playlists.Count)
        test_playlist = playlists.ItemByName('test_playlist')
        print(test_playlist.Tracks.Count)
        play_lists = []
        tp_count = test_playlist.Tracks.Count
        print("Test Playlist")
        oids = []
        for i in range(1, tp_count+1):
            print(test_playlist.Name, test_playlist.playlistID)
            track = test_playlist.Tracks.Item(i)
            oid = track.GetITObjectIDs()
            oids.append(oid)
            print(f"run delete")
            print("Track to delete: ", track.Name, oid, track.KindAsString, track.Playlist.Name)
            play_lists.append((track.sourceID, track.playlistID, 0, 0))
        
        
        deleted_oids = []
        for oid in oids:
            track = self.itunes.GetITObjectByID(*oid)
            track.Delete() # removes track from playlist
            # library_ttrack.Delete() # removes track from library

        for play_list in playlists:
            if play_list.playlistID in play_lists:
                print(play_list.Name)

        library_tracks = self.itunes.LibraryPlaylist.Tracks
        lt_count = library_tracks.Count
        print("remaining tracks")
        for i in range(1, lt_count+1):
            track = library_tracks.Item(i)
            t_pid = self.itunes.GetITObjectPersistentIDs(track)
            if track.Name == 'SUSMAN=V2':
                print(track.Name, track.sourceID, track.playlistID, track.trackID, track.TrackDatabaseID, track.KindAsString, t_pid)

        