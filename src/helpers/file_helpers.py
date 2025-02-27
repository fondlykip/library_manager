import copy
import os
import pathlib
from pathlib import Path
import shutil
import logging
from zipfile import ZipFile
import config


DEFAULT_TYPES = ['wav', 'mp3', 'aiff']


def common_lineage(path_1: Path,
                   path_2: Path):
    p1_splits = str(path_1.absolute()).split('/')
    p2_splits = str(path_2.absolute()).split('/')
    logging.debug(f"Finding common lineage between {path_1.absolute()} and {path_2.absolute()}")
    max_common = min(len(p2_splits), len(p1_splits))
    p1_splits = p1_splits[len(p1_splits)-max_common:]
    p2_splits = p2_splits[len(p2_splits)-max_common:]
    assert len(p1_splits) == len(p2_splits)
    common_folders = ""
    for i in range(0,max_common).__reversed__():
        logging.info(i)

def get_folders(path: Path, 
                recursive: bool = True, 
                full_path: bool = True):
    """Function to get a list of folders
    available at a given path
    Args:
        path (str): the path for which we want to get
                    a list of folders
        recursive (bool): Boolean flag to make the search
                          recursive
                          True: function is recalled
        full_path (bool): Boolean flag to return full path#
                          or file names.
                          True: returns lists of path objects
                          False: reutrns lists of file names
    Returns:
        ouput_folders (list): A list of folders available 
                              at the Path"""
    log_id = f"{__name__}.get_folders"
    logging.debug(f"get folders for {path}")
    if not path.is_dir():
        logging.debug(f'{log_id} | Object is not a dir: {path.absolute()}')
        return None

    obj_list = path.iterdir()
    output_paths = []
    for obj in obj_list:
        if full_path:
            insert_obj = obj
        else:
            insert_obj = obj.name 

        if not obj.is_dir():
            continue

        output_paths.append(insert_obj)

        if recursive:
            sub_dir_list = get_folders(obj, recursive, full_path)
            output_paths.extend(sub_dir_list)

    return output_paths


def get_files(path: Path, 
              search_types: list = DEFAULT_TYPES,
              recursive: bool = True):
    """Function to get a list of files
    available at a given path
    Args:
        path (str): the path for which we want to get
                    a list of files
    Returns:
        ouput_folders (list): A list of files available 
                              at the Path"""
    obj_list = path.iterdir()
    found_files = []
    for obj in obj_list:
        logging.debug(obj.name)
        if obj.is_dir() and recursive:
            found_files.extend(get_files(obj, search_types, recursive))
            continue
        elif obj.is_dir():
            continue

        if (not search_types) or (len(search_types) == 0):
            found_files.append(obj)
            continue
        
        if any([obj.name.endswith(ftype) for ftype in search_types]):
            found_files.append(obj)
  
    return found_files


def extract_file(file: Path,
                 output_path: Path = None):
    """Function to extract a zip file to either the given
    output folder, or the folder where the zip file is
    currently located.
    Args:
        file (Path): file to extract
        output_path (Path): folder to extract the file to
                              Default: None - same folder as zip
                                       location
    Returns:
        output_path (Path): Folder where the zip file was extracted to
        None (NoneType): Failure mode
    """
    log_id = f"{__name__}.extract_file"
    if file.is_dir():
        logging.debug(f"""{log_id} | Invalid input: object is a directory
                            - {file.absolute()}""")
        return None

    if not file.name.endswith('.zip'):
        logging.debug(f"""{log_id} | object is not a zip file
                            - {file.absolute()}""")
        return None

    if not output_path:
        output_path = Path(str(file.absolute())[:-4])
    else:
        output_path = Path(str(output_path.absolute())).joinpath(file.name[:-4])
        logging.info(f"ouput to {output_path.absolute()}")
    
    _ = output_path.mkdir(exist_ok=True)

    if not output_path.is_dir():
        logging.debug(f"""{log_id} | Output folder is not a directory
                            - {output_path.absolute()}""")
        return None        
    
    with ZipFile(file.absolute(), 'r') as f:
        logging.debug(f"""{log_id} | Extracting {file.name}
                            - {file.absolute()} > {output_path.absolute()}""")
        f.extractall(output_path)
        logging.debug(f"""{log_id} | Extraction finished for {file.name}
                            - {output_path.absolute()}""")        

    return output_path


def bulk_extract(in_dir: Path,
                 out_dir: Path = None):
    logging.debug(f"Start Bulk Extraction")

    if not in_dir:
        logging.debug("Input path must not be None")
        return False
    
    if not in_dir.is_dir():
        logging.debug("input path must be a dir")
        return False
    
    if type(out_dir) != type(Path()) and out_dir != None:
        logging.debug("Output must be path or None")
        return False
    
    if out_dir:
        extracted = get_folders(out_dir, False, True)
    else:
        extracted = get_folders(in_dir, False, True)
    
    logging.debug(f"found {len(extracted)} folders in destination")

    for obj in in_dir.iterdir():
        output = None

        if obj.name.endswith('.zip'):
            obj_path = Path(str(obj.absolute())[:-4])
            logging.info(obj_path)
            if obj_path.exists():
                logging.debug(f"Skip {obj.name}")
                continue
            else:
                logging.debug(f"check path: |{obj_path.absolute()}| -  {obj_path.exists()}")

            logging.debug(f"extract {obj}")
            output = extract_file(obj, out_dir)

        if output:
            logging.debug(f"Unzipped {obj.name} to {output}")

    return True


def move_files(src_path: Path,
               dest_path: Path,
               contents_only: bool = False):
    """Function to move file from given source path to a
    given destination path. if contents_only is set to False,
    the contents of the file at the Source path will be moved
    to the folder specified as the dest_path.
    Args:
        src_path (Path): Current Path of the file or folder
        dest_path (Path): Destination Path of the file
        contents_only (Bool): Boolean flag to only move the
                              contents of the source folder
                              to the dest folder
    Returns:
        new_path (Path): New location of moved file
        None (NoneType): Error mode
    """
    log_id = f"{__name__}.move_files"

    if not src_path.exists():
        logging.debug(f"""{log_id} | 404 Source file not found
                                - {src_path.absolute()}""")
        return None
    
    if not dest_path.exists():
        dest_path.mkdir(parents=True, exist_ok=True)

    if not dest_path.is_dir():
        logging.debug(f"""{log_id} | Destination must be a directory
                            - {dest_path.absolute()}""")
        return None
    
    if not src_path.is_dir():
        try:
            output_path_str = shutil.move(src_path.absolute(), dest_path.absolute())
            output_path = Path(output_path_str)
            return output_path
        except shutil.Error as e:
            logging.debug(f"""{log_id} | Unable to move files - Shutil Error: {e.strerror}
                                - {src_path.absolute()} > {dest_path.absolute()}""")
    
    if not contents_only:
        try:
            output_path_str = shutil.move(src_path.absolute(), dest_path.absolute())
            output_path = Path(output_path_str)
            return output_path
        except shutil.Error as e:
            logging.debug(f"""{log_id} | Unable to move files - Shutil Error: {e.strerror}
                                - {src_path.absolute()} > {dest_path.absolute()}""")
    
    for obj in src_path.iterdir():
        try:
            _ = shutil.move(obj.absolute(), dest_path.absolute())
        except shutil.Error as e:
            logging.debug(f"""{log_id} | Unable to move files - Shutil Error: {e.strerror}
                                - {obj.absolute()} > {dest_path.absolute()}""")
    
    return dest_path

    
def validate_path(path_str: str, 
                  must_exist: bool = True):
    if not type(path_str) == str:
        logging.info(f"Paths must be strings: {path_str} ({type(path_str)})")
        return False
    path = Path(path_str)
    if must_exist and not path.exists():
        logging.info(f"Path must exist for this context: {path_str}")
        return False
    return True


MAIN_FOLDER = 'C:/Users/liamj/Documents/DJ Music/'
output_path = 'E:/clean_dj_music_2/'



