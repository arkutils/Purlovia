import os.path
from configparser import ConfigParser

from .stream import MemoryStream
from .asset import UAsset, ImportTableItem, ExportTableItem
from .base import UEBase
from .properties import ObjectProperty, ObjectIndex, Property

from ark.asset import findComponentExports

__all__ = ('AssetLoader', 'load_file_into_memory')


class AssetLoader:
    def __init__(self, configpath: str = '.', quiet=False):
        self.cache = dict()
        self.configpath = configpath
        self.quiet = quiet
        self._load_user_config()
        self._load_mods_config()

    def clean_asset_name(self, name: str):
        name = name.strip().replace('\\', '/').strip('/')

        # Remove .uasset, if present
        if name.lower().endswith('.uasset'):
            name = name[:-7]

        # Remove asset_path, if present
        if name.lower().startswith(self.normalised_asset_path):
            name = name[len(self.normalised_asset_path):]

        parts = name.strip('/').split('/')

        # Convert mod names to numbers
        if len(parts) > 2 and parts[1].lower() == 'mods' and parts[2].isnumeric():
            parts[2] = self.mods_numbers_to_names[parts[2]]

        # Change Content back to name, for cache consistency
        if len(parts) and parts[0].lower() == 'content':
            parts[0] = 'Game'

        name = '/'.join(parts)
        name = '/' + name

        return name

    def wipe_cache(self):
        self.cache = dict()

    def convert_asset_name_to_path(self, name: str, partial=False):
        '''Get the filename from which an asset can be loaded.'''
        name = self.clean_asset_name(name)
        parts = name.strip('/').split('/')

        # Convert mod names to numbers
        if len(parts) > 2 and parts[1].lower() == 'mods' and not parts[2].isnumeric():
            parts[2] = self.mods_names_to_numbers[parts[2]]

        # Game is replaced with Content
        if len(parts) and parts[0].lower() == 'game':
            parts[0] = 'Content'

        fullname = os.path.join(self.asset_path, *parts)
        if not partial:
            fullname += '.uasset'

        return fullname

    def get_mod_name(self, assetname):
        assert assetname is not None
        assetname = self.clean_asset_name(assetname)
        parts = assetname.strip('/').split('/')
        if len(parts) < 3:
            return None
        if parts[0].lower() != 'game' or parts[1].lower() != 'mods':
            return None
        mod = parts[2]
        if mod.isnumeric():
            mod = self.mods_numbers_to_names[mod]
        return mod

    def get_mod_descriptive_name(self, assetname):
        assert assetname is not None
        assetname = self.clean_asset_name(assetname)
        parts = assetname.strip('/').split('/')
        if len(parts) < 3:
            return None
        if parts[0].lower() != 'game' or parts[1].lower() != 'mods':
            return None
        mod = parts[2]
        id = mod
        if not mod.isnumeric():
            id = self.mods_names_to_numbers[mod]
        description = self.mods_numbers_to_descriptions.get(id, mod)
        return description

    def find_assetnames(self, regex, toppath='/', exclude=None):
        import re
        toppath = self.convert_asset_name_to_path(toppath, partial=True)
        for path, dirs, files in os.walk(toppath):
            for filename in files:
                fullpath = os.path.join(path, filename)
                name, ext = os.path.splitext(fullpath)

                if not ext.lower() == '.uasset': continue
                match = re.match(regex, name)
                if not match: continue
                if exclude:
                    exclude_match = re.match(exclude, name)
                    if exclude_match: continue

                assetname = self.clean_asset_name(fullpath)
                yield assetname

    def load_related(self, obj: UEBase):
        if isinstance(obj, Property):
            return self.load_related(obj.value)
        if isinstance(obj, ObjectProperty):
            return self.load_related(obj.value.value)
        if isinstance(obj, ImportTableItem):
            assetname = str(obj.namespace.value.name.value)
            loader = obj.asset.loader
            asset = loader[assetname]
            return asset
        raise ValueError("Invalid type")

    def _set_asset_path(self, path):
        self.asset_path = path

    def _load_raw_asset_from_file(self, filename: str):
        '''Load an asset given its filename into memory without parsing it.'''
        if not self.quiet: print("Loading file:", filename)
        if not os.path.isabs(filename):
            filename = os.path.join(self.asset_path, filename)
        mem = load_file_into_memory(filename)
        return mem

    def _load_raw_asset(self, name: str):
        '''Load an asset given its asset name into memory without parsing it.'''
        name = self.clean_asset_name(name)
        if not self.quiet: print("Loading asset:", name)
        filename = self.convert_asset_name_to_path(name)
        mem = load_file_into_memory(filename)
        return mem

    def __getitem__(self, assetname: str):
        '''Load and parse the given asset, or fetch it from the cache if already loaded.'''
        assetname = self.clean_asset_name(assetname)
        asset = self.cache.get(assetname, None) or self._load_asset(assetname)
        return asset

    def _load_asset(self, assetname: str):
        mem = self._load_raw_asset(assetname)
        stream = MemoryStream(mem, 0, len(mem))
        asset = UAsset(stream)
        asset.loader = self
        asset.assetname = assetname
        asset.name = assetname.split('/')[-1]
        asset.deserialise()
        asset.link()
        exports = list(findComponentExports(asset))
        if len(exports) > 1:
            import warnings
            warnings.warn(f'Found more than one component in {assetname}!')
        asset.default_export = exports[0] if len(exports) else None
        self.cache[assetname] = asset
        return asset

    def _load_user_config(self):
        config = ConfigParser()
        config.read(os.path.join(self.configpath, 'user.ini'))
        asset_path = config.get('parser', 'assetpath', fallback='.')
        if not self.quiet: print("Using asset path: " + asset_path)
        self.asset_path = asset_path
        self.normalised_asset_path = asset_path.lower().replace('\\', '/').lstrip('/')

    def _load_mods_config(self):
        config = ConfigParser(inline_comment_prefixes='#;')
        config.optionxform = lambda v: v  # keep exact base of mod names, please
        config.read(os.path.join(self.configpath, 'mods.ini'))
        self.mods_numbers_to_names = dict(config['ids'])
        self.mods_names_to_numbers = dict(reversed(kvp) for kvp in config['ids'].items())
        self.mods_numbers_to_descriptions = dict(config['names'])


def load_file_into_memory(filename):
    with open(filename, 'rb') as f:
        data = f.read()
        mem = memoryview(data)
        return mem
