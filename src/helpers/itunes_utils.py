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

    def xml_to_dict(self, element, node):
        # Parse attributes
        Element.attrib
        node.update(element.attrib.items())
        curr_key = None
        for child in element:
            if child.tag == 'key':
                key_val = child.text.strip()
                node[key_val] = None
                curr_key = child.text.strip()

            elif child.tag == 'string':
                node[curr_key] = str(child.text)

            elif child.tag == 'integer':
                node[curr_key] = int(child.text)

            elif child.tag == 'true':
                node[curr_key] = True

            elif child.tag == 'false':
                node[curr_key] = False

            elif child.tag == 'date':
                node[curr_key] = str(child.text)

            elif child.tag == 'dict':
                key = curr_key if curr_key is not None else 'data'
                child_node = {}
                updated_child_node = self.xml_to_dict(child, child_node)
                node[key] = updated_child_node

            elif child.tag == 'array':
                node_array = [self.xml_to_dict(gchild, {}) for gchild in child]
                node[curr_key] = node_array

        return node


    def dict_to_xml(self, f,
                    dic: dict,
                    #parent: ET.Element = None,
                    is_root: bool = True,
                    level: int = 0):
        """Function to rebuild iTunes XML File post
        changes being made to the XML
        Args:
            dic (dict): dictionary to parse
            level (int): how deep into the tree we are
            parent (Element)
        """
        indent = "".join('\t' for i in range(0,level))
        if is_root:
            data = dic['data']
            header_str ="""<?xml version="1.0" encoding="UTF-8"?>\n"""\
                        """<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n"""\
                        f"""<plist version="{dic['version']}">\n"""\
                            "<dict>\n"
            f.write(header_str)
            _ = self.dict_to_xml(f, data, False, level+1)
            footer_str = """</dict>\n"""\
                         """</plist>"""
            f.write(footer_str)
            return True

        for key, value in dic.items():

            if isinstance(value, bool):
                line_str = f"{indent}<key>{str(key)}</key><{str(value).lower()}/>\n"
                f.write(line_str)

            elif isinstance(value, dict):
                line_str = f"{indent}<key>{key}</key>\n"\
                           f"{indent}<dict>\n"
                f.write(line_str)
                _ = self.dict_to_xml(f, value, False, level+1)
                close_line_str = f"{indent}</dict>\n"
                f.write(close_line_str)

            elif isinstance(value, list):
                line_str = f"{indent}<key>{str(key)}</key>\n"\
                            f"{indent}<array>\n"
                f.write(line_str)
                for dic in value:
                    dic_str = f"{indent}\t<dict>\n"
                    f.write(dic_str)
                    _ = self.dict_to_xml(f, dic, False, level+2)
                    dic_str = f"{indent}\t</dict>\n"
                    f.write(dic_str)
                
                line_str = f"{indent}</array>\n"

            elif is_date(value):
                line_str = f"{indent}<key>{str(key)}</key><date>{str(value)}</date>\n"
                f.write(line_str)

            else:
                tag = 'string' if isinstance(value, str) else 'integer'
                line_str = f"{indent}<key>{str(key)}</key><{tag}>{value}</{tag}>\n"
                f.write(line_str)

        return True


    def parse_xml(self, path: Path):
        # IF its o
        tree = ET.parse(path)
        root = tree.getroot()
        node = {}
        parsed_xml = self.xml_to_dict(root, node)
        return parsed_xml


    def parse_dict(self, xmld: dict):
        tree = ET.ElementTree()
        root = self.dict_to_xml(xmld)
        tree._setroot(root)
        return tree


    def save_library(self, output_path: Path = None):
        if output_path is None:
            output_path = self.library_xml_loc

        with open(output_path, "a", encoding='utf-8') as f:
            success = self.dict_to_xml(f, self.library_dict)

        return output_path


    def get_library_csvs(self, output_path: Path) -> Path:
        library_tracks = copy.deepcopy(self.library_dict['data']['Tracks'])
        playlists = copy.deepcopy(self.library_dict['data']['Playlists'])
        file_timestamp = datetime.now().strftime("%Y%m%d%H%M")
        track_cols = []
        for id, data in library_tracks.items():
            for col in data.keys():
                if col not in track_cols:
                    track_cols.append(str(col))
        print(track_cols)
        track_cols = set(track_cols)
        h_row = '\t'.join(col.lower().replace(' ', '_') for col in track_cols)
        h_row += '\n'
        l_t_filename = output_path / f'/library_tracks_{file_timestamp}.csv'

        with open(l_t_filename, 'w', encoding='utf-8') as f:
            f.write(h_row)

        row_count = 0
        for _, data in library_tracks.items():
            row_d = []
            for col in track_cols:
                val = data.get(col, None)
                row_d.append(val)
            row_s = '\t'.join([str(v) for v in row_d])
            row_s += '\n'
            with open(l_t_filename, 'a', encoding='utf-8') as f:
                f.write(row_s)
            row_count += 1
        print(f'{row_count} rows written to {l_t_filename}')

        playlist_cols = []
        for playlist in playlists:
            for col in playlist.keys():
                if col not in playlist_cols and col != 'Playlist Items':
                    playlist_cols.append(str(col))

        playlist_cols = set(playlist_cols)
        h_row = '\t'.join(col.lower().replace(' ', '_') for col in playlist_cols)
        h_row += '\n'
        pl_filename = output_path / f'/playlists_{file_timestamp}.csv'
        with open(pl_filename, 'w', encoding='utf-8') as f:
            f.write(h_row)
        
        row_count = 0
        for data in playlists:
            row_d = []
            for col in playlist_cols:
                if col == "Playlist Items":
                    continue
                val = str(data.get(col, None))
                row_d.append(val)
            row_s = '\t'.join([v for v in row_d])
            row_s += '\n'
            with open(pl_filename, 'a', encoding='utf-8') as f:
                f.write(row_s)
            row_count += 1
        print(f'{row_count} rows written to {pl_filename}')

        p_map_file = output_path / f'/playlist_track_mapping_{file_timestamp}.csv'
        with open(p_map_file, 'w') as f:
            f.write('playlist_id\ttrack_id\n')
        row_count = 0
        with open(p_map_file, 'a') as f:
            for playlist in playlists:
                plist_id = playlist['Playlist ID']
                tracks = playlist.get('Playlist Items', [])
                for track in tracks:
                    f.write(f'{plist_id}\t{track["Track ID"]}\n')
                    row_count += 1
        print(f'{row_count} rows written to {p_map_file}')

        print("Library successfully written to CSVs")
        output_dict = {
                        'library_tracks': l_t_filename,
                        'playlists': pl_filename,
                        'playlist_tracks': p_map_file
                    }
        return output_dict


    def apply_mapping(self, csv_path):
        # Remap the tracks based on the mappings in the csv at the path
        mapping_dict = {}
        with open(csv_path, 'r') as f:
            for idx, line in enumerate(f.readlines()):
                if idx == 0:
                    continue
                track_id, aif_id = line.replace('\n', '').split('\t')
                mapping_dict[str(track_id)] = str(aif_id)
                print(f"mapping found: {track_id} {type(track_id)}, {aif_id} {type(aif_id)}")
        
        print(mapping_dict)

        for playlist in self.library_dict['data']['Playlists']:
            if playlist['Name'] in self.skip_playlists:
                continue

            remapped_tracks = 0
            for track in playlist['Playlist Items']:
                print(f"Track ID: {track['Track ID']} | {type(track['Track ID'])}")
                mapping = mapping_dict.get(str(track['Track ID']), None)
                if not mapping:
                    continue

                track['Track ID'] = mapping
                remapped_tracks += 1
            print(f"Remapped {remapped_tracks} tracks in playlist {playlist['Name']}")


    def backup_itunes_data(self, backup_path: Path, backup_media: bool = False):
        for object in backup_path.iterdir():
            if any(object.name.endswith(x) for x in ['itdb', 'itl', 'xml', 'plist']):
                return None



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
