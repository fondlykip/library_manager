"""
Main entry point into the application
"""
from src.helpers import itunes_utils_v2
from pathlib import Path

def main():
    DRY_RUN = False
    print("init Itunes Application")
    itunes = itunes_utils_v2.ITunesLibrary()
    #itunes.test_playlist_operations()
    print("Get Itunes DFs")
    itunes.get_library_dfs()

    print("Run Matching")
    matches = itunes.run_matching()
    print(f"{matches.shape[0]} matches found")
    print(f"{matches['playlist_name'].unique()}")
    print("export dfs for analysis")
    itunes.export_csvs(Path('./src/data/'))

    print(f"replaced matched files in user playlists | dry_run {DRY_RUN}")
    itunes.run_match_fix(matches, add_aifs=True, delete_matches= True, delete_lib_tracks = True, dry_run=DRY_RUN)

    # print(f"delete matched tracks from library_tracks | dry_run {DRY_RUN}")
    # itunes.delete_matched_library_tracks(dry_run=DRY_RUN)
    # itunes.test_playlist_operations()

if __name__ == "__main__":
    main()
