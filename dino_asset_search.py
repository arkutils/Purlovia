import os

from ue.loader import AssetLoader


def main():
    loader = AssetLoader()

    count = 0
    for path, dirs, files in os.walk(loader.asset_path):
        for filename in files:
            if filename.endswith('.uasset') and '_Character_BP' in filename:
                fullpath = os.path.join(path, filename)
                asset = loader[fullpath]

                count += 1
                if count % 10 == 0:
                    input()


if __name__ == '__main__':
    main()
