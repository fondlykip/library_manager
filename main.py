"""
Main entry point into the application
"""
from src.helpers import itunes_utils_v2
from pathlib import Path

def main():
    DRY_RUN = True
    print("init Itunes Application")
    itunes = itunes_utils_v2.ITunesLibrary()

    print("Get Itunes DFs")
    itunes.get_library_dfs()

    print("Run Matching")
    num_matches = itunes.run_matching()
    print(f"{num_matches} matches found")

    print("export dfs for analysis")
    itunes.export_csvs(Path('./src/data/'))

    print(f"replaced matched fils in user playlists | dry_run {DRY_RUN}")
    itunes.replace_matches(dry_run=DRY_RUN)

    print(f"delete matched tracks from library_tracks | dry_run {DRY_RUN}")
    itunes.delete_matched_library_tracks(dry_run=DRY_RUN)
    #itunes.test_playlist_operations()

if __name__ == "__main__":
    main()
