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
import io


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
                'name': playlist.Name,
                'source_id': playlist.sourceID
            }
            playlist_data.append(playlist_dict)
            plist_tracks = playlist.Tracks
            pltrack_count = plist_tracks.Count
            for i in range(1, pltrack_count+1):
                plist_track = plist_tracks.Item(i)
                plist_mapping = {
                    'playlist_id': plist_id,
                    'track_id': plist_track.trackID,
                    'track_database_id': plist_track.TrackDatabaseID,
                    'track_source_id': plist_track.sourceID
                }
                plist_mappings.append(plist_mapping)

        self.playlists = pd.DataFrame(playlist_data)
        self.playlist_track_mapping = pd.DataFrame(plist_mappings)
        print("playlist and track mapping created")
        return True

    def get_lib_track(self, plist_track):
        plist_track_oid = plist_track.GetITObjectIDs()
        plist_track_pid = self.itunes.GetITObjectPersistentIDs(plist_track)
        pt_name = plist_track.Name
        print(f"""Playlist Track: {pt_name}
                object IDs (src ID, plist ID, trk ID, trk db ID): {plist_track_oid}
                persistent IDs: {plist_track_pid}
               """)
        lp_tracks = self.itunes.LibraryPlaylist.Tracks
        lpt = lp_tracks.ItemByPersistentID(plist_track_pid)
        lpt_pid = self.itunes.GetITObjectPersistentIDs(lpt)
        lpt_name = lpt.Name
        lpt_kind = lpt.KindAsString
        lpt_oids = lpt.GetITObjectIDs()
        print(f"""Library Track: {lpt_name} ({lpt_kind})
                object IDs (src ID, plist ID, trk ID, trk db ID): {lpt_oids}
                persistent IDs: {lpt_pid}
               """)
        return lpt

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
                df.to_csv(output_path / file_name, index=False)


    def get_media_locations(self):
        tracks = self.itunes.LibrarySource.Tracks
        print(tracks.Count)

    def replace_matches(self, dry_run: bool = True):
        new_plist_tracks = []
        inserted_aifs = []
        deleted_plist_tracks = []
        updated_plists = []
        for idx, match in self.matches.iterrows():
            plist_oid = (match['playlist_source_id'],
                         match['playlist_id'], 0, 0)
            new_track_oid = (match['aif_source_id'],
                             match['aif_playlist_id'],
                             match['aif_track_id'],
                             match['aif_database_id'])
            old_track_oid = (match['track_source_id'],
                             match['track_playlist_id'],
                             match['track_id'],
                             match['track_database_id'])
            plist = self.itunes.GetITObjectByID(*plist_oid)
            new_track = self.itunes.GetITObjectByID(*new_track_oid)
            old_track = self.itunes.GetITObjectByID(*old_track_oid)
            
            if new_track.KindAsString != 'AIFF audio file' \
              or old_track.KindAsString == 'AIFF audio file' :
                raise Exception(
                    "Not Mapping a new AIFF File or Would remove an AIFF File"
                    )
    
            if old_track.playlistID != plist.playlistID\
              and old_track.sourceID != plist.sourceID:
                raise Exception(
                    f"Old track {old_track.Name}, {old_track.TrackDatabaseID}"\
                    f" does not belong to playlist {plist.Name}, {plist.playlistID}"
                    )
    
            print('----------------------------------------------------------------------------')
            print(f"add new track {new_track.Name} ({new_track.KindAsString}) to {plist.Name}")
            
            if dry_run:
                npt_oid = (plist.sourceID,
                           plist.playlistID,
                           new_track.trackID,
                           new_track.TrackDatabaseID)
                print("dry_run = True | Skipping Adding Track")
                print(f"generated expected Object ID: {npt_oid}")
            else:
                print("Adding track to playlist")
                new_plist_track = plist.AddTrack(new_track)
                npt_oid = new_plist_track.GetITObjectIDs()
                print(f"Done! returned Object ID: {npt_oid}")
        
            new_plist_tracks.append(npt_oid)
            lib_aif_oid = new_track.GetITObjectIDs()
            inserted_aifs.append(lib_aif_oid)
            print(f"replace old track {old_track.Name} ({old_track.KindAsString}) in {plist.Name}")
            print(f"matched on: {match['match_type']}")
            old_file = str(old_track.Location).encode('utf-8')
            new_file = str(new_track.Location).encode('utf-8')
            print(f"old file: {old_file}")
            print(f"new file: {new_file}")

            deleted_oid = old_track.GetITObjectIDs()

            if dry_run:
                print("dry_run = True | Skipping Deleting Track")
            else:
                print(f"Deleting {old_track.Name} from {plist.Name}")
                old_track.Delete()
            
            deleted_plist_tracks.append(deleted_oid)
            print("Deleted")
            print('----------------------------------------------------------------------------')
            updated_plist_oid = plist.GetITObjectIDs()
            updated_plists.append(updated_plist_oid)
        
        unique_updated_plists = set(updated_plists)
        unique_inserted_aifs = set(inserted_aifs)
        print(f"{len(unique_inserted_aifs)} AIFF Files"\
              f" added in {len(unique_updated_plists)} playlists")
        
        data_dir = './src/data/'
        file_timestamp = datetime.now().strftime("%Y%m%d%H%M")
    
        added_file = Path(f"{data_dir}added-{file_timestamp}.csv")
        added_file.touch()
        with open(added_file, 'w+', encoding='utf-8') as f:
            for line in new_plist_tracks:
                f.write(str(line))
        
        deleted_file = Path(f"{data_dir}deleted-{file_timestamp}.csv")
        deleted_file.touch()
        with open(deleted_file, 'w+', encoding='utf-8') as f:
            for line in deleted_plist_tracks:
                f.write(str(line))
        
        total_added = len(new_plist_tracks)
        total_deleted = len(deleted_plist_tracks)
        print(f"{total_added} objects added to iTunes DB, {total_deleted} deleted")

    def delete_matched_library_tracks(self):
        for idx, match_row in self.matches:
            plist_track_oid = (
                match_row['track_source_id'],
                match_row['track_playlist_id'],
                match_row['track_id'],
                match_row['track_database_id']
            )
            plist_track = self.itunes.GetITObjectByID(
                *plist_track_oid
            )
            plist_track_pid = self.itunes.GetITObjectPersistentIDs(plist_track)


    # def test_playlist_operations(self):
    #     playlists = self.itunes.LibrarySource.Playlists
    #     p_count = playlists.Count
    #     for i in range(1, p_count+1):
    #         if playlists.Item(i).Name == 'test_playlist':
    #             print(i)
    #             print(playlists.Item(i).Name)
    #             test_playlist = playlists.Item(i)
    #             print(test_playlist.Tracks.Count)
    #             tp_pids = self.itunes.GetITObjectPersistentIDs(test_playlist)
    #             print(tp_pids)
    #     print('Library Tracks')
    #     library_tracks = self.itunes.LibraryPlaylist.Tracks
    #     lt_count = library_tracks.Count
    #     at_oids = []
    #     for i in range(1, lt_count+1):
    #         track = library_tracks.Item(i)
    #         if track.Name == 'SUSMAN=V2':
    #             t_oid = track.GetITObjectIDs()
    #             kind = track.KindAsString
    #             if kind == 'AIFF audio file':
    #                 added_track = test_playlist.AddTrack(track)
    #                 at_oid = added_track.GetITObjectIDs()
    #                 at_oids.append(at_oid)
    #                 print(f"Track added, {test_playlist.Tracks.Count}")

    #                 print("Add Track to test playlist", added_track.Name, added_track.GetITObjectIDs(), added_track.KindAsString, added_track.Playlist.Name, at_oid, t_oid)
    #     print(tp_pids)
    #     print(playlists.Count)
    #     test_playlist = playlists.ItemByName('test_playlist')
    #     print(test_playlist.Tracks.Count)
    #     play_lists = []
    #     tp_count = test_playlist.Tracks.Count
    #     print("Test Playlist")
    #     oids = []
    #     for i in range(1, tp_count+1):
    #         print(test_playlist.Name, test_playlist.playlistID)
    #         track = test_playlist.Tracks.Item(i)
    #         oid = track.GetITObjectIDs()
    #         oids.append(oid)
    #         print(f"run delete")
    #         print("Track to delete: ", track.Name, oid, track.KindAsString, track.Playlist.Name)
    #         play_lists.append((track.sourceID, track.playlistID, 0, 0))
        
        
    #     deleted_oids = []
    #     for oid in oids:
    #         track = self.itunes.GetITObjectByID(*oid)
    #         track.Delete() # removes track from playlist
    #         # library_ttrack.Delete() # removes track from library

    #     for play_list in playlists:
    #         if play_list.playlistID in play_lists:
    #             print(play_list.Name)

    #     library_tracks = self.itunes.LibraryPlaylist.Tracks
    #     lt_count = library_tracks.Count
    #     print("remaining tracks")
    #     for i in range(1, lt_count+1):
    #         track = library_tracks.Item(i)
    #         t_pid = self.itunes.GetITObjectPersistentIDs(track)
    #         if track.Name == 'SUSMAN=V2':
    #             print(track.Name, track.sourceID, track.playlistID, track.trackID, track.TrackDatabaseID, track.KindAsString, t_pid)

        