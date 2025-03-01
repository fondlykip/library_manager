"""
Main entry point into the application
"""
from src.helpers import itunes_utils_v2
from pathlib import Path

def main():
    print("init Itunes Application")
    itunes = itunes_utils_v2.ITunesLibrary()
    # print("Get Itunes DFs")
    # itunes.get_library_dfs()
    # print("Run Matching")
    # num_matches = itunes.run_matching()
    # print(f"{num_matches} matches found")
    # #itunes.export_csvs(Path('./'))
    # itunes.replace_matches()
    itunes.test_playlist_operations()

if __name__ == "__main__":
    main()
