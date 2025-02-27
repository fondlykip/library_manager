import pytest
from pathlib import Path
import logging
import copy


def setup_folder(config: dict,
                 path: Path,
                 folder_id: str = '1',
                 built_layers: int = 0):
    total_objects = 0
    for file in config['files']:
        file_name = f'{folder_id}_file.{file}'
        file_path = path.joinpath(file_name)
        file_path.touch()
        total_objects += 1

    if built_layers == config['depth']:
        return total_objects

    for i in range(1,config['breadth']+1):
        folder_name = f'fol_{i}/'
        new_path = Path(f'{path.absolute()}/{folder_name}')
        new_path.joinpath(folder_name)
        new_path.mkdir(parents=True,
                       exist_ok=True)
        bl = built_layers + 1
        new_id = f'{folder_id}{i}'
        total_objects += setup_folder(config,
                                      new_path,
                                      new_id,
                                      bl)
    return total_objects


def teardown_folder(path: Path):
    for obj in path.iterdir():
        if obj.is_dir():
            teardown_folder(obj)
            obj.rmdir()
        else:
            obj.unlink()
    

@pytest.fixture(scope='class')
def setup_files():
    config = {
        'root': './test_dir/',
        'breadth': 3,
        'depth': 3,
        'files': ['mp3', 'wav', 'txt', 'aiff']
    }
    root_path = Path(config['root'])
    root_path.mkdir(exist_ok=True)
    created_objects = setup_folder(config,
                                   root_path)
    logging.info(f'created {created_objects + 1} in setup: {root_path.absolute()}')
    yield config
    logging.info(f'tearing down test directories')
    teardown_folder(root_path)
    root_path.rmdir()
    logging.info('finished tearing down test folder setup')



    


