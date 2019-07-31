from tkinter import Tk

from gui.tree_frame import TreeFrame


class MainApplication(Tk):
    def __init__(self):
        super().__init__()
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.minsize(width=600, height=400)
        self.geometry('800x900')

        self.frame = TreeFrame(self)

    def load_asset(self, assetname, loader):
        assetname = loader.clean_asset_name(assetname)
        self.title("Asset Browser : " + assetname)
        asset = loader[assetname]
        self.frame.load_asset(asset)
