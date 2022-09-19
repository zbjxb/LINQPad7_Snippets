#!/bin/sh
# -*- coding: utf-8 -*-

import os
from typing import NoReturn, Optional
from git import Repo, index
from datetime import date
from pathlib import Path

try:
    import chardet
except:
    os.system("pip install chardet")
    import chardet

import random
import string


def get_plugins_need_update(plugins: list[str], git_root_folder: str, staged_files: list[str]) -> list[str]:
    """Check the plugins which need updating the version number.
    
    Parameters
    ----------
    plugins : list of string
        Absolute paths of the plugin files
    git_root_folder : string
        The absolute path of the root folder of the git repository
    staged_files : list of string
        The files in staged area. Paths relative to git_root_folder.

    Return
    ------
    Absolute paths of the uplugin files which need updating.
    """

    local_need_update_plugins = []
    # print('checking>>>')
    for p in plugins:
        plugin_root = str(Path(p).parent)
        # print('plugin_root is: ' + plugin_root)
        for sf in staged_files:
            absp = str(Path(git_root_folder) / sf)
            # print('absolute path: ' + absp)
            if absp.startswith(plugin_root):
                local_need_update_plugins.append(p)
                break

    # print('<<<')
    return local_need_update_plugins


def breadth_first_search_uproject_folder(dirs: list[str]) -> Optional[str]:
    local_dirs = []

    for d in dirs:
        with os.scandir(d) as it:
            for entry in it:
                if entry.is_file() and entry.name.endswith('.uproject'):
                    print('uproject file is: ' + entry.name)
                    return d
                elif entry.is_dir():
                    local_dirs.append(entry)
                else:
                    pass
    
    dirs.clear()

    if len(local_dirs) == 0:
        return None
    else:
        return breadth_first_search_uproject_folder(local_dirs)


def get_uproject_folder(root: str) -> Optional[str]:
    """Get the absolute path of uproject file resides.

    Search the uproject type file recursively in root, 
    and return the absolute path of the folder which the 
    first found file resides.

    Warning
    -------
    This method requires that there's only one unreal project in git repository.

    Parameters
    ----------
    root : string
        Absolute path

    Return
    ------
    An optional absolute path.
    """

    dirs: list[str] = [root]
    return breadth_first_search_uproject_folder(dirs)


def breadth_first_get_uplugins(dirs: list[str], results: list[str]) -> NoReturn:
    local_dirs = []

    for d in dirs:
        with os.scandir(d) as it:
            local_entries = []
            bFound = False

            for entry in it:
                if entry.is_file() and entry.name.endswith('.uplugin'):
                    bFound = True
                    results.append(entry.path)
                    break
                elif entry.is_dir():
                    local_entries.append(entry)
                else:
                    pass

            if not bFound:
                local_dirs.extend(local_entries)

    dirs.clear()

    if len(local_dirs) != 0:
        breadth_first_get_uplugins(local_dirs, results)


def get_uplugins(folder: str) -> list[str]:
    """Get uplugin files.
    
    Search all uplugin files recursively in folder, but 
    the subfolders won't be searched once a folder contains uplugin file.
    
    Parameters
    ----------
    folder : string
        Absolute path

    Return
    ------
    Absolute paths of all uplugin files.
    """

    plugins_filelist = []
    breadth_first_get_uplugins([folder], plugins_filelist)

    return plugins_filelist


def get_staged_files(repo: Repo) -> list[str]:
    """Get the files in staged area.

    Return
    ------
    Paths relative to GIT_ROOT_FOLDER of repo.
    """

    local_staged_files = []
    diffindex_obj = repo.index.diff('HEAD')
    for d in diffindex_obj.iter_change_type('A'):
        local_staged_files.append(d.b_path)

    for d in diffindex_obj.iter_change_type('D'):
        local_staged_files.append(d.a_path)

    for d in diffindex_obj.iter_change_type('C'):
        local_staged_files.append(d.b_path)

    for d in diffindex_obj.iter_change_type('R'):
        local_staged_files.append(d.a_path)

    for d in diffindex_obj.iter_change_type('M'):
        local_staged_files.append(d.a_path)

    return local_staged_files


def stage_files(repo: Repo, files: list[str]) -> None:
    """Add the files to staged area.

    Parameters
    ----------
    repo : Repo
        Git repository
    files : list of string
        Absolute paths
    """

    index_lock_file = Path(repo.git_dir)/"index.lock"
    if index_lock_file.exists():
        print("\n**********************\nErrors occurred. The pre-commit-hook detected the 'index.lock' file. Please commit the modified uplugin files manually.\n***********************\n")
    else:
        repo.index.add(files)


def step_version(uplugin_file: str, new_version: str) -> None:
    """Change the version field of the uplugin file.

    Parameters
    ----------
    uplugin_file : string
        Absolute path of the plugin file.
    new_version : string
        The new version number.
    """

    cur_encoding = 'utf-8'
    with open(uplugin_file, 'rb') as frb:
        cur_encoding = chardet.detect(frb.read())['encoding']

    raw_lines : list[str] = []
    with open(uplugin_file, 'r', encoding=cur_encoding) as file_to_read:
        file_buf = file_to_read.read()
        raw_lines = file_buf.splitlines(True)

    version_changed: bool = False
    for index, raw_line in enumerate(raw_lines):
        if 'VersionName' in raw_line:
            if raw_line != new_version:
                version_changed = True
                raw_lines[index] = new_version
                break
            else:
                print("Skip.")
                return

    if version_changed:
        with open(uplugin_file, 'w', encoding=cur_encoding) as file_to_write:
            file_to_write.write("".join(raw_lines))
            file_to_write.flush()
            print("Changed.")
    else:
        print("VersionName field not found in uplugin file. Skip.")


def get_version(repo: Repo) -> str:
    """Create a unique version number based on the latest commit."""

    local_head_commit_hexsha : str = ""

    local_head_commit = repo.head.commit
    if local_head_commit is None:
        local_head_commit_hexsha = "0000000"
    else:
        local_head_commit_hexsha = local_head_commit.hexsha[0:7]

    rs = random.sample(string.hexdigits, k=6)
    local_version_field_value = '{date}#{hex}#{rnd}'.format(date=date.today().strftime("%b-%d-%Y"), hex=local_head_commit_hexsha, rnd="".join(rs))
    local_version = '\t"VersionName": "{desc}",\n'.format(desc=local_version_field_value)
    return local_version


def pre_commit() -> NoReturn:
    curr_dir = Path(__file__).parent.absolute() # git-action-hooks folder
    my_repo = Repo(curr_dir, search_parent_directories=True)

    my_staged_files = get_staged_files(my_repo)
    # print('staged files:>>>')
    # print(my_staged_files)
    # print('<<<')
    if len(my_staged_files) == 0:
        print("There's no staged changes.")
        return

    uproject_folder = get_uproject_folder(my_repo.working_dir)
    if uproject_folder is None:
        print("This repository contains no unreal projects.")
        return

    plugins_root = os.path.join(uproject_folder, 'Plugins')
    plugin_files = get_uplugins(plugins_root)
    if len(plugin_files) == 0:
        print("This unreal project contains no plugins.")
        return
    else:
        print('plugins:>>>')
        print(plugin_files)
        print('<<<\n')

    need_update_plugins = get_plugins_need_update(plugin_files, my_repo.working_dir, my_staged_files)
    if len(need_update_plugins) == 0:
        print("There's no plugins need to update.")
        return
    else:
        print('need update plugins:>>>')
        print(need_update_plugins)
        print('<<<\n')

    print("Changing version...")
    new_version_number = get_version(my_repo)
    for p in need_update_plugins:
        step_version(p, new_version_number)

    stage_files(my_repo, need_update_plugins)
    print("...Done")


if __name__ == '__main__':
    print('\npre-commit hooks log:>>>>>>>>>>>>>>>>>>>>\n')
    pre_commit()
    print('\n<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<\n')
