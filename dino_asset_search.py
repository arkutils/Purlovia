import re
import os

from browseasset import *

PATH = r"G:\Programs\Steam\steamapps\common\ARK\ShooterGame\Content"

if __name__ == '__main__':
    global loader
    loader = AssetLoader()

    count = 0
    for path, dirs, files in os.walk(PATH):
        for filename in files:
            if filename[-7:] != '.uasset':
                continue
            if not '_Character_BP' in filename:
                continue

            fullpath = os.path.join(path, filename)

            # print(fullpath)
            load_asset(fullpath, loader)

            count += 1
            if count is 10:
                count = 0
                os.system("pause")
