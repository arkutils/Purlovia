import sys
from typing import Any

# pylint: disable=import-outside-toplevel,global-statement,import-error

#%% Run this cell first to use VSCode's interactive mode
is_interactive = bool(getattr(sys, 'ps1', sys.flags.interactive))
pprint = None
pretty = None


def configure_ipython_width():
    global pretty, pprint

    ipy: Any = None
    try:
        from IPython import get_ipython  # type: ignore
        ipy = get_ipython()
    except (ModuleNotFoundError, ImportError):
        ...

    if ipy and 'ZMQInteractiveShell' in str(ipy):  # Notebook-like IPython shell
        import IPython.lib.pretty  # type: ignore
        pprint = IPython.lib.pretty.pprint
        pretty = IPython.lib.pretty.pretty
        ipy.config.PlainTextFormatter.max_width = 140
        print("! Forcing wrap width for non-shell view to:", ipy.config.PlainTextFormatter.max_width)
        from IPython.core.interactiveshell import InteractiveShell  # type: ignore
        InteractiveShell.instance().init_display_formatter()
        return

    import shutil
    w, _h = shutil.get_terminal_size()

    if ipy:  # IPython shell
        import IPython.lib.pretty  # type: ignore
        pprint = IPython.lib.pretty.pprint
        pretty = IPython.lib.pretty.pretty
        print("Setting IPython to terminal width:", w)
        ipy.config.PlainTextFormatter.max_width = w - 1
        return

    # Plain python shell
    from pprint import pformat as opretty
    from pprint import pprint as opprint

    if is_interactive:
        print("Wrapping pprint with terminal width:", w)

    def _pprint(obj, **user_kwargs):
        return opprint(obj, **{'width': w - 1, **user_kwargs})

    def _pretty(obj, **user_kwargs):
        return opretty(obj, **{'width': w - 1, **user_kwargs})

    pretty = _pretty
    pprint = _pprint


configure_ipython_width()
del configure_ipython_width

# %%
