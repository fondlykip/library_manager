"""
Main entry point into the application
"""
from src.helpers import itunes_utils_v2
from pathlib import Path
import copy
from pywintypes import com_error
import win32api

def main():
    DRY_RUN = False
    print("init Itunes Application")
    itunes = itunes_utils_v2.ITunesLibrary()
    itunes_app = itunes.itunes

    pt_oid = (69, 35908, 36052, 7130) # src_id, pl_id, t_id, t_db_id
 
    pt = itunes_app.GetITObjectByID(*pt_oid)
    lpt = itunes.get_lib_track(pt)
    # print("Get Itunes DFs")
    # itunes.get_library_dfs()
    # print("Run Matching")
    # num_matches = itunes.run_matching()
    # print(f"{num_matches} matches found")
    # itunes.export_csvs(Path('./src/data/'))
    # itunes.replace_matches(dry_run=DRY_RUN)
    #itunes.test_playlist_operations()

if __name__ == "__main__":
    main()
