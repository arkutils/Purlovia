from tkinter import ttk

from gui.tree import Tree


class TreeFrame(ttk.Frame):
    def __init__(self, parent, *args, padding: str = '6 6 6 6', **kwargs):
        super().__init__(parent, padding=padding, **kwargs)
        self.grid(column=0, row=0, sticky='nsew')
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.tree = Tree(self)

    def load_asset(self, asset):
        # Load the asset
        self.tree.add_asset_to_root(asset)
