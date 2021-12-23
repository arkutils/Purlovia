if __name__ == '__main__':
    import os
    import sys

    if len(sys.argv) <= 1:
        print('Usage: python -m interactive <script file>', file=sys.stderr)
        sys.exit(1)

    # sys.path.insert(0, os.getcwd())
    from interactive_utils import *

    with open(sys.argv[1], 'rt', encoding='utf-8') as f:
        exec(f.read())  # pylint: disable=exec-used  # dev utility only
