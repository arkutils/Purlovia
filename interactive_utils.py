import os, sys
from IPython.lib.pretty import pretty, pprint


def configure_ipython_width():
    from IPython import get_ipython
    ipy = get_ipython()
    if 'ZMQInteractiveShell' in str(ipy):  # Notebook-like
        ipy.config.PlainTextFormatter.max_width = 140
        print("! Forcing wrap width for non-shell view to:", ipy.config.PlainTextFormatter.max_width)
        from IPython.core.interactiveshell import InteractiveShell
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
