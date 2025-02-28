import helpers
from src.helpers import tag_utils
from pathlib import Path
import shutil
from src.helpers import file_helpers as f_help
from src.helpers.itunes_utils import ITunesLibrary
import json
from struct import unpack

# for each file in the source
# determine what its filename in itunes will be using tags


def clean_aif_dir():
    clean_dir = "E:\\aif_library\\"
    itunes_dir = "C:\\Users\\liamj\\Music\\iTunes\\iTunes Media\\Music\\"

    clean_path = Path(clean_dir)
    for file in f_help.get_files(clean_path,
                                 ['.aiff']):
        id3_tags = tag_utils.get_tags(file.absolute())
    return False


itunes_dir = "C:\\Users\\liamj\\Music\\iTunes\\iTunes Media\\Music\\"
backup_dir = "E:\\iTunes-backup\\iTunes\\iTunes Media\\Music\\"
def restore_itunes(itunes_dir,
                   backup_dir):
    backup_files = f_help.get_files(backup_dir)
    saved_files = 0
    for file in backup_files:
        relative_path = file.relative_to(backup_dir)
        check_path = Path(itunes_dir) / relative_path
        if not check_path.exists():
            #print(f"copy {file} to {check_path}")
            shutil.copy(file, check_path)
            saved_files += 1

    print(f"{saved_files} files saved!")


def remap_plist_tracks(csv_path: Path, library: ITunesLibrary):
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

    for playlist in library.library_dict['data']['Playlists']:
        if playlist['Name'] in library.skip_playlists:
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


        
    



if __name__=='__main__':
    #clean_aif_dir()
    #restore_itunes(Path(itunes_dir), Path(backup_dir))
    # with open(Path("C:\\Users\\liamj\\Music\\iTunes\\iTunes Library.itl"), 'rb') as f:
    #     fileContent = f.read()

    # with open(Path("C:\\Users\\liamj\\Music\\iTunes\\iTunes_Library_itl.txt"), 'w') as o:
    #     o.write(str(fileContent))

    itunes_lib = ITunesLibrary()
    itunes_lib.get_library_dfs()
    itunes_lib.export_csvs('C:\\Users\\liamj\\Desktop\\')

    # mapping_csv = Path("C:\\Users\\liamj\\Music\\plist_track_aif_mapping.csv")
    # library = ITunesLibrary()
    # library.apply_mapping(mapping_csv)


    # library.get_library_csvs(Path("E:\\"))
    # saved_path = library.save_library(Path(itunes_dir)/ "new_library.xml")
    # print(saved_path)
