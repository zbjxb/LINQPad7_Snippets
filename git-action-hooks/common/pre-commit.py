#!/bin/sh
# -*- coding: utf-8 -*-

import os
from re import template
from typing import NoReturn, Optional
from git import Repo, index
from datetime import date
from pathlib import Path
import json

try:
    import chardet
except:
    os.system("pip install chardet")
    import chardet

import random
import string

stars = "*************************"

curr_dir = Path(__file__).parent.absolute() # config.template.json folder
my_repo = Repo(curr_dir, search_parent_directories=True)
GIT_ROOT_FOLDER = Path(my_repo.working_dir)
CONFIG_PATH = curr_dir / "config.json"

def is_modifications(repo: Repo) -> bool:
    """ Check if there's some modifications.

    Return
    ------
    True if any modifications exist. Otherwise return False.
    """

    diffindex_obj = repo.index.diff('HEAD')
    if diffindex_obj != None:
        return len(diffindex_obj) > 0
    else:
        return False


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
        print(stars)
        print("Errors occurred. The pre-commit-hook detected the 'index.lock' file. Please commit the modified uplugin files manually.")
        print(stars)
    else:
        repo.index.add(files)


def change_version(config: object, new_version: str) -> bool:
    """Change the version field of the version file.

    Parameters
    ----------
    config: object
        Describe the version file template, placeholder and output version file.
        It's a json object. Reference the config.template.json file.
    new_version : string
        The new version number.

    Return
    ------
    True if outputs version file success. Otherwise return False.
    """

    template_file = None
    if "template" not in config:
        print(stars)
        print("[template] field not exist")
        return False

    template_file = GIT_ROOT_FOLDER / config["template"]
    if not template_file.exists():
        print(stars)
        print("Error occurs: The template file not exist.")
        return False

    cur_encoding = 'utf-8'
    with open(str(template_file), 'rb') as frb:
        cur_encoding = chardet.detect(frb.read())['encoding']

    file_buf = None
    with open(str(template_file), 'r', encoding=cur_encoding) as file_to_read:
        file_buf = file_to_read.read()

    placeholder = None
    if "placeholder" not in config:
        print(stars)
        print("[placeholder] field not exist.")
        return False

    placeholder = config["placeholder"]
    file_buf = file_buf.replace(placeholder, new_version)

    output_file = None
    if "output" not in config:
        print(stars)
        print("[output] field not exist.")
        return False

    output_file = GIT_ROOT_FOLDER / config["output"]
    with open(str(output_file), 'w', encoding=cur_encoding) as file_to_write:
        file_to_write.write(file_buf)
        file_to_write.flush()
        print("Changed.")

    return output_file.exists()


def get_version_value(repo: Repo) -> str:
    """Create a unique version number based on the latest commit."""

    local_head_commit_hexsha : str = ""

    local_head_commit = repo.head.commit
    if local_head_commit is None:
        local_head_commit_hexsha = "0000000"
    else:
        local_head_commit_hexsha = local_head_commit.hexsha[0:7]

    rs = random.sample(string.hexdigits, k=6)
    local_version_field_value = '{date}#{hex}#{rnd}'.format(date=date.today().strftime("%b-%d-%Y"), hex=local_head_commit_hexsha, rnd="".join(rs))
    return local_version_field_value


def pre_commit() -> NoReturn:
    if not is_modifications(my_repo):
        print(stars)
        print("There's no modifications.")
        return

    if not CONFIG_PATH.exists():
        print(stars)
        print("config.json not exists.")
        return

    print("Changing version...")

    cur_encoding = 'utf-8'
    with open(str(CONFIG_PATH), 'rb') as frb:
        cur_encoding = chardet.detect(frb.read())['encoding']

    config = None
    with open(str(CONFIG_PATH), 'r', encoding=cur_encoding) as f:
        config = json.load(f)

    if config == None:
        print(stars)
        print("Read config.json failure.")
        return

    new_version_number = get_version_value(my_repo)

    version_files = []
    for key, value in config.items():
        if key == "version_files":
            for c in value:
                if change_version(c, new_version_number):
                    version_files.append(str(GIT_ROOT_FOLDER / c["output"]))

    stage_files(my_repo, version_files)
    print("...Done")


if __name__ == '__main__':
    print('\npre-commit hooks log:>>>>>>>>>>>>>>>>>>>>\n')
    pre_commit()
    print('\n<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<\n')
