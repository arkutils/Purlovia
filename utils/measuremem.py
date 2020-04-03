'''
A utility to measure the memory usage of a Python snippet, in a style similar to `timeit`.

Usage: measuremem.py <setup snippet> <measured snippet>

(remember to use quotes to encapsulate each statememt)
'''

import os
import sys
from typing import Any, Dict, List

from guppy import hpy

from .resource_monitor import resource_monitor

SRC_NAME = '<cmdline>'

TMPL = '''
def inner():
    {setup}
    hp = hpy()
    hp.setrelheap()
    with resource_monitor():
        {article}
    h = hp.heap()

    return h.size
'''


def main(args: List[str]) -> int:
    if len(args) != 3:
        print("Usage: measuremem.py <setup snippet> <measured snippet>", file=sys.stderr)
        sys.exit(1)

    setup_snippet = args[1] or 'pass'
    article_snippet = args[2]

    sys.path.insert(0, os.curdir)

    # Verify they each compile
    compile(setup_snippet, SRC_NAME, "exec")
    compile(article_snippet, SRC_NAME, "exec")

    # Make up the runnable snippet
    src = TMPL.format(setup=setup_snippet, article=article_snippet)
    code = compile(src, SRC_NAME, "exec")
    local_ns: Dict[str, Any] = dict()
    exec(code, globals(), local_ns)  # noqa  # pylint: disable=exec-used
    inner_fn = local_ns['inner']

    # Run it and display the result
    heap = inner_fn()
    print(heap)

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
