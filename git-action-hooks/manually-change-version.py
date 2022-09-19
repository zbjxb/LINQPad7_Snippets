# -*- coding: utf-8 -*-

import os
from typing import NoReturn, Optional
from git import Repo, index
from datetime import date
from pathlib import Path


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


def step_version(uplugin_file: str, new_version: str) -> None:
    """Change the version field of the uplugin file.

    Parameters
    ----------
    uplugin_file : string
        Absolute path of the plugin file.
    new_version : string
        The new version number.
    """

    raw_lines : list[str] = []
    with open(uplugin_file, 'r', encoding='utf-8') as file_to_read:
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
        with open(uplugin_file, 'w', encoding='utf-8') as file_to_write:
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


def manually_change_version() -> NoReturn:
    curr_dir = Path(__file__).parent.absolute()
    my_repo = Repo(curr_dir, search_parent_directories=True)

    plugin_files = get_uplugins(curr_dir)
    if len(plugin_files) == 0:
        print("No plugins found.")
        return
    else:
        print('plugins:>>>')
        print(plugin_files)
        print('<<<')

    print("Changing version...")
    new_version_number = get_version(my_repo)
    for p in plugin_files:
        step_version(p, new_version_number)

    print("...Done")


if __name__ == '__main__':
    manually_change_version()
