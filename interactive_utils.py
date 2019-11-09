import os
import sys

from IPython.lib.pretty import pprint, pretty  # type: ignore


def configure_ipython_width():
    from IPython import get_ipython  # type: ignore
    ipy = get_ipython()
    if 'ZMQInteractiveShell' in str(ipy):  # Notebook-like
        ipy.config.PlainTextFormatter.max_width = 140
        print("! Forcing wrap width for non-shell view to:", ipy.config.PlainTextFormatter.max_width)
        from IPython.core.interactiveshell import InteractiveShell  # type: ignore
        InteractiveShell.instance().init_display_formatter()
    elif ipy:  # IPython shell
        import shutil
        w, h = shutil.get_terminal_size()
        print("Setting IPython to terminal width:", w)
        ipy.config.PlainTextFormatter.max_width = w - 1
    else:  # Plain python shell
        import shutil
        w, h = shutil.get_terminal_size()
        print("Wrapping pprint with terminal width:", w)
        global pretty, pprint
        opretty = pretty
        opprint = pprint

        def _pprint(obj, **user_kwargs):
            kwargs = dict(max_width=w - 1)
            kwargs.update(user_kwargs)
            return opprint(obj, **kwargs)

        def _pretty(obj, **user_kwargs):
            kwargs = dict(max_width=w - 1)
            kwargs.update(user_kwargs)
            return opretty(obj, **kwargs)

        pretty = _pretty
        pprint = _pprint


configure_ipython_width()
del configure_ipython_width


def printjson(obj):
    import json
    import pygments  # type: ignore
    formatted = obj if isinstance(obj, str) else json.dumps(obj, indent=4)
    out = pygments.highlight(formatted, pygments.lexers.JsonLexer(), pygments.formatters.TerminalFormatter())
    print(out)
