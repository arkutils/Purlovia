import os
from pathlib import Path, PurePosixPath

from config import get_global_config
from ue.loader import AssetLoader, AssetNotFound

__all__ = [
    'find_asset_from_external_path',
]


def find_asset_from_external_path(assetname: str, loader: AssetLoader, allow_tk=False):
    if not assetname and allow_tk:
        try:
            from tkinter import filedialog
        except ImportError:
            raise AssetNotFound('No asset name specified')

        assetname = filedialog.askopenfilename(title='Select asset file...',
                                               filetypes=(('uasset files', '*.uasset'), ("All files", "*.*")),
                                               initialdir=loader.asset_path / 'Content')
        if not assetname:
            raise AssetNotFound('No asset selected')

    # Attempt to work around MingW hijacking /Game as a root path
    if assetname.startswith('//'):
        assetname = assetname[1:]
    if 'MINGW_PREFIX' in os.environ:
        mingw_base = Path(os.environ['MINGW_PREFIX']).parent
        try:
            path = Path(assetname).relative_to(mingw_base)
            assetname = str(PurePosixPath(path))
        except ValueError:
            pass

    # Try it as-is first
    try:
        clean_assetname = loader.clean_asset_name(assetname)
        asset = loader[clean_assetname]
        return asset.assetname
    except Exception:  # pylint: disable=broad-except
        pass

    # Try a combination of possible roots
    asset_path_options: tuple[Path, ...] = (
        Path(assetname),
        Path(assetname).absolute(),
        Path(assetname).resolve(),
    )

    search_paths: tuple[str | Path, ...] = (
        '.',
        Path(get_global_config().settings.DataDir / 'game/ShooterGame'),
        loader.asset_path,
        loader.absolute_asset_path,
    )

    for asset_path in asset_path_options:
        for search_path in search_paths:
            clean_path = relative_path(asset_path, search_path)
            if not clean_path:
                continue

            clean_path = clean_path.with_suffix('')
            assetname = str(PurePosixPath(clean_path))

            try:
                asset = loader[assetname]
                return asset.assetname
            except AssetNotFound:
                continue

    raise AssetNotFound(assetname)


def relative_path(path: Path | str, root: Path | str) -> Path | None:
    try:
        return Path(path).relative_to(root)
    except ValueError:
        return None
