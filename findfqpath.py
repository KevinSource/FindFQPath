#! python3
# Finds the current the most current version of a file
# Once it's found, it will be stored in a shelf file
# Future calls pull from the shelf file first, then search if the file is older than requested
# or the file is missing

import os
import sys
import shelve
import shutil
import logging
from pathlib import Path
from shelve import DbfilenameShelf
from typing import List, Optional, Union
import datetime
from datetime import timedelta

import platformdirs

# ********************************************************************************************************
# * Set up logging
# * To turn on logging, set root_logger.disabled = False
# * To turn off logging, set root_logger.disabled = True
# ********************************************************************************************************
root_logger = logging.getLogger()
root_logger.disabled = False
logging.basicConfig(level=logging.DEBUG, format=' %(asctime)s - %(levelname)s - %(message)s')

# ********************************************************************************************************
# * Folders that should never be walked
# * Windows: WinSxS holds duplicate copies of system files, the Recycle Bin holds deleted ones
# * Linux/macOS: virtual file systems
# ********************************************************************************************************
if sys.platform == 'win32':
    SKIP_DIRS = {os.path.join(os.environ.get('SYSTEMROOT', r'C:\Windows'), 'WinSxS'),
                 os.path.join(os.environ.get('SYSTEMDRIVE', 'C:') + os.sep, '$Recycle.Bin')}
else:
    SKIP_DIRS = {'/proc', '/sys', '/dev', '/run'}
SKIP_DIRS = {os.path.normcase(path) for path in SKIP_DIRS}


def default_search_dirs() -> List[str]:
    # ********************************************************************************************************
    # * The usual install locations for this OS. Only folders that exist are returned
    # ********************************************************************************************************
    home = str(Path.home())
    if sys.platform == 'win32':
        candidates = [os.environ.get('PROGRAMFILES', r'C:\Program Files'),
                      os.environ.get('PROGRAMFILES(X86)', r'C:\Program Files (x86)'),
                      os.path.join(os.environ.get('LOCALAPPDATA', os.path.join(home, 'AppData', 'Local')),
                                   'Programs')]
    elif sys.platform == 'darwin':
        candidates = ['/Applications', os.path.join(home, 'Applications'), '/usr/local/bin', '/opt/homebrew/bin']
    else:
        candidates = ['/usr/bin', '/usr/local/bin', '/opt', '/snap/bin', os.path.join(home, '.local', 'bin')]
    return [path for path in candidates if os.path.isdir(path)]


def filesystem_root() -> str:
    # ********************************************************************************************************
    # * The last resort search location: the system drive on Windows, / everywhere else
    # ********************************************************************************************************
    if sys.platform == 'win32':
        return os.environ.get('SYSTEMDRIVE', 'C:') + os.sep
    return os.sep


def find_under(search_from_path: str, find_file: str) -> List[str]:
    # ********************************************************************************************************
    # * Return every file named find_file below search_from_path
    # * Unreadable folders are skipped, symlinked folders are not followed
    # ********************************************************************************************************
    logging.debug('About to search for file %s in: %s', find_file, search_from_path)
    target = os.path.normcase(find_file)
    found_file_list = []
    for dir_path, dir_names, file_names in os.walk(search_from_path):
        dir_names[:] = [d for d in dir_names if os.path.normcase(os.path.join(dir_path, d)) not in SKIP_DIRS]
        found_file_list.extend(os.path.join(dir_path, f) for f in file_names if os.path.normcase(f) == target)
    logging.debug('Matches found for file %s is %d', find_file, len(found_file_list))
    return found_file_list


# ********************************************************************************************************
# *
# * find_fq_path: will return a full qualified path or None
# * find_file: Name of the file to find (ie. opera.exe on Windows, opera on Linux, Opera on macOS)
# * num_days_valid: Trigger a new search if the data in the shelf file is older than this number of days
# *                  0 will always trigger a new search
# * Scope: "Local" will save the fully qualified path in the project folder and only be found by the
# *         script in that folder
# *         "Shared" or any other value will save the fully qualified path in the user's cache folder
# *         and be referenced from all other scripts that use "Shared"
# *
# ********************************************************************************************************


def find_fq_path(find_file, num_days_valid, scope="Shared") -> Optional[str]:
    # ********************************************************************************************************
    # *
    # * This figures out where the shelf file is and gets the data if it's there
    # *
    # ********************************************************************************************************
    if scope.upper() == "LOCAL":
        shelf_path: Union[bytes, str] = os.path.dirname(os.path.realpath(sys.argv[0]))
        logging.debug('Script Directory:' + shelf_path)
    else:
        shelf_path = platformdirs.user_cache_dir('findfqpath', appauthor=False)
        os.makedirs(shelf_path, exist_ok=True)
        logging.debug('Shared Directory:' + shelf_path)

    pathkey = find_file + 'fqpath'
    path_update_date_key = find_file + 'DateUpdated'
    shelf_nm = os.path.join(shelf_path, 'FileShlf')
    logging.debug('Shelf File Name: %s', shelf_nm)
    find_file_path_shelf: DbfilenameShelf = shelve.open(shelf_nm)

    # ********************************************************************************************************
    # * Get the fully qualified path of the file and the date it was stored
    # ********************************************************************************************************
    found_file_list = []
    if pathkey in find_file_path_shelf:
        curr_find_file_path = find_file_path_shelf[pathkey]
        curr_path_last_update_dt = find_file_path_shelf[path_update_date_key]

        #  ********************************************************************************************************
        #  * See if the file still exists and see if it is recent enough to use, if so, return the
        #  * fully qualified path and quit
        #  ********************************************************************************************************
        test_file = Path(curr_find_file_path)
        if test_file.is_file() and datetime.datetime.now() < \
                curr_path_last_update_dt + timedelta(days=num_days_valid):
            logging.debug('Find File Name Location: %s', curr_find_file_path)
            find_file_path_shelf.close()
            return curr_find_file_path

    # ********************************************************************************************************
    # * Check the PATH first. It's instant and is what the OS itself would run
    # ********************************************************************************************************
    which_path = shutil.which(find_file)
    if which_path:
        logging.debug('Found on PATH: %s', which_path)
        found_file_list = [os.path.abspath(which_path)]
    elif pathkey in find_file_path_shelf:
        # ********************************************************************************************************
        # * Search from two directory levels up from where it was found before, then keep
        # * going up a level until it's found or the top of the drive is reached
        # ********************************************************************************************************
        logging.debug('Entering Search for file: %s', curr_find_file_path)
        search_from_path = os.path.dirname(os.path.dirname(curr_find_file_path))
        while True:
            found_file_list = find_under(search_from_path, find_file)
            parent_path = os.path.dirname(search_from_path)
            if found_file_list or parent_path == search_from_path:
                break
            search_from_path = parent_path
    else:
        # ********************************************************************************************************
        # * First time for this file: search the usual install folders, then the whole drive
        # ********************************************************************************************************
        for search_from_path in default_search_dirs():
            found_file_list.extend(find_under(search_from_path, find_file))
        if not found_file_list:
            found_file_list = find_under(filesystem_root(), find_file)

    # ********************************************************************************************************
    # * Find the most recent version of the file, write the info to the shelf file and return the
    # * fully qualified file and path
    # ********************************************************************************************************
    if len(found_file_list) > 0:
        curr_find_file_path = max(found_file_list, key=os.path.getmtime)
        find_file_path_shelf[pathkey] = curr_find_file_path
        find_file_path_shelf[path_update_date_key] = datetime.datetime.now()
        find_file_path_shelf.close()
        return curr_find_file_path
    else:
        # * Couldn't find it, return None
        find_file_path_shelf.close()
        return None


if __name__ == "__main__":
    #Adobe_file_path = find_fq_path(find_file='AcroRd32.exe', num_days_valid=1,scope="Shared")
    opera_file_path = find_fq_path(find_file='opera.exe', num_days_valid=1,scope="Shared")
    logging.debug('Path for requested file: %s', opera_file_path)
