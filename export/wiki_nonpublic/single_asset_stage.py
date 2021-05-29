from abc import ABCMeta, abstractmethod
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Optional

from automate.exporter import ExportStage
from automate.jsonutils import save_json_if_changed
from automate.version import createExportVersion
from ue.asset import UAsset
from ue.gathering import gather_properties
from ue.proxy import UEProxyStructure
from ue.utils import sanitise_output
from utils.log import get_logger

logger = get_logger(__name__)


class SingleAssetExportStage(ExportStage, metaclass=ABCMeta):
    @abstractmethod
    def get_asset_name(self) -> str:
        '''Return the fullname of the asset to load.'''
        ...

    @abstractmethod
    def get_format_version(self) -> str:
        '''Return the a format version identifier.'''
        ...

    def get_core_file_path(self) -> PurePosixPath:
        '''Return the relative path of the core output file that should be generated.'''
        name = self.get_name()
        return PurePosixPath(f'{name}.json')

    @abstractmethod
    def get_use_pretty(self) -> bool:
        '''Return True if the file should be prettified, or False if it should be minified.'''
        ...

    @abstractmethod
    def extract(self, proxy: UEProxyStructure) -> Optional[Dict[str, Any]]:
        '''Perform extraction on the given proxy and return a JSON-able dict.'''
        raise NotImplementedError

    def extract_core(self, path: Path):
        '''Perform extraction for core (non-mod) data.'''

        # Work out the output path (cleaned)
        output_path = Path(path / self.get_name()).with_suffix('.json')

        # Core versions are based on the game version and build number
        version = createExportVersion(self.manager.arkman.getGameVersion(), self.manager.arkman.getGameBuildId())  # type: ignore

        # Setup the output structure
        format_version = self.get_format_version()
        output: Dict[str, Any] = dict()
        output['version'] = version
        output['format'] = format_version

        # Load the asset and grab a proxy
        asset: UAsset = self.manager.loader[self.get_asset_name()]
        assert asset.default_class and asset.default_export
        proxy: UEProxyStructure = gather_properties(asset)

        # Do the actual export
        item_output = self.extract(proxy)

        if item_output:
            # Sanitise and join with the output dict.
            sanitised: Dict[str, Any] = sanitise_output(item_output)
            output.update(sanitised)

            # Save if the data changed
            save_json_if_changed(output, output_path, self.get_use_pretty())
        else:
            # Remove an existing file as the output is empty
            if output_path.is_file():
                output_path.unlink()
            return

    def extract_mod(self, path, modid):
        # Not supported at the moment. Do nothing.
        ...
