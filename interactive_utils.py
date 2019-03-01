from IPython.lib.pretty import pretty, pprint

def configure_ipython_width_in_notebook():
    from IPython import get_ipython
    ipy = get_ipython()
    if 'ZMQInteractiveShell' in str(ipy):
        print("! Forcing wrap width for non-shell view")
        ipy.config.PlainTextFormatter.max_width = 140
        from IPython.core.interactiveshell import InteractiveShell
        InteractiveShell.instance().init_display_formatter()

configure_ipython_width_in_notebook()
del configure_ipython_width_in_notebook
