import pytest
from pathlib import Path
import logging
from src.helpers import file_helpers as f_help
from tests.conftest import setup_files

class TestFolderUtils:

    def test_get_folders(self, setup_files):
        root_path = Path(setup_files['root'])
        result = f_help.get_folders(root_path, False)
        assert len(result) == setup_files['breadth']
 

    def test_get_folders_recursion(self, setup_files):
        root_path = Path(setup_files['root'])
        result = f_help.get_folders(root_path, True)
        breadth = setup_files['breadth']
        depth = setup_files['depth']
        exp_len = sum([pow(breadth, n) for n in range(1,depth+1)])
        res_len = len(result)
        assert res_len == exp_len


    def test_get_folder_names(self, setup_files):
        root_path = Path(setup_files['root'])
        result = f_help.get_folders(root_path,
                                    False,
                                    False)
        for item in result:
            assert type(item) == type(str())
    

    def test_get_folder_paths(self, setup_files):
        root_path = Path(setup_files['root'])
        result = f_help.get_folders(root_path,
                                    False,
                                    True)
        for item in result:
            assert type(item) == type(Path())


    def test_get_files(self, setup_files):
        root_path = Path(setup_files['root'])
        result = f_help.get_files(path=root_path,
                                  search_types=setup_files['files'],
                                  recursive=False)
        assert len(result) == len(setup_files['files'])


    def test_get_files_recursive(self, setup_files):
        root_path = Path(setup_files['root'])
        result = f_help.get_files(path=root_path,
                                  search_types=setup_files['files'],
                                  recursive=True)
        breadth = setup_files['breadth']
        depth = setup_files['depth']
        num_f_types = len(setup_files['files'])
        exp_len = num_f_types + sum([num_f_types*pow(breadth, n) for n in range(1,depth+1)])
        assert len(result) == exp_len