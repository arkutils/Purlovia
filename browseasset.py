import sys

from gui.main_application import MainApplication

from automate.ark import ArkSteamManager

if __name__ == '__main__':
    arkman = ArkSteamManager()
    loader = arkman.createLoader()

    assetname = sys.argv[1] if len(sys.argv) > 1 else None

    root = MainApplication()
    root.withdraw()

    if not assetname:
        from tkinter import filedialog
        from pathlib import Path
        assetname = filedialog.askopenfilename(title='Select asset file...',
                                               filetypes=(('uasset files', '*.uasset'), ("All files", "*.*")),
                                               initialdir=loader.asset_path)
        assert assetname
        path = Path(assetname).relative_to(loader.asset_path).with_suffix('')
        assetname = str(path)

    root.load_asset(assetname, loader)

    root.deiconify()

    root.mainloop()
