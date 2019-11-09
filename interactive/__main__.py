if __name__ == '__main__':
    import os
    import sys

    if len(sys.argv) <= 1:
        print(f'Usage: python -m interactive <script file>', file=sys.stderr)
        sys.exit(1)

    # sys.path.insert(0, os.getcwd())
    from interactive_utils import *

    with open(sys.argv[1], "r") as f:
        exec(f.read())  # pylint: disable=exec-used  # dev utility only
