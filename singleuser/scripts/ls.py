#!/usr/bin/env python3

import sys
import json
import os
import argparse
from os import path


USER_DIR = '/home/jovyan'


def getFileSystemData(dir_path, p_path):
    _children = os.listdir(path=dir_path)
    if len(_children) == 0:
        return _children
    children = []
    for child in filter(lambda x: not x.startswith('.'), _children):
        if checkExtension(child, ".job"):
            children.append(buildChild(text=child, f_type="job", p_path=p_path))
        elif checkExtension(child, ".mdl"):
            children.append(buildChild(text=child, f_type="nonspatial", p_path=p_path))
        elif checkExtension(child, ".smdl"):
            children.append(buildChild(text=child, f_type="spatial", p_path=p_path))
        elif checkExtension(child, ".mesh"):
            children.append(buildChild(text=child, f_type="mesh", p_path=p_path))
        elif checkExtension(child, ".ipynb"):
            children.append(buildChild(text=child, f_type="notebook", p_path=p_path))
        elif path.isdir(path.join(dir_path, child)):
            children.append(buildChild(text=child, f_type="folder", p_path=p_path))
        else:
            children.append(buildChild(text=child, f_type="other", p_path=p_path))
    return children


def buildChild(text, f_type, p_path):
    if p_path == "/":
        p_path = ""
    child = { 'text' : text, 'type' : f_type, '_path' : '{0}/{1}'.format(p_path, text) }
    child['children'] = f_type == "folder"
    return child


def checkExtension(data, target):
    if data.endswith(target):
        return True
    else:
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get the content of a directory and create JSTree nodes for item that are not hidden.")
    parser.add_argument('path', help="The path from the user directory to the target directory.")
    args = parser.parse_args()
    p_path = args.path
    dir_path = path.join(USER_DIR, p_path)
    data = getFileSystemData(dir_path, p_path)
    print(json.dumps(data))
