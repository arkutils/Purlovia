from abc import ABCMeta, abstractmethod
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterator, List, Optional, Type

from pydantic import BaseModel, Field

from automate.jsonutils import save_json_if_changed
from automate.version import createExportVersion
from ue.proxy import UEProxyStructure
from ue.utils import sanitise_output
from utils.strings import get_valid_filename

from .exporter import ExportStage

__all__ = [
    'Field',
    'ExportModel',
    'ExportFileModel',
    'JsonHierarchyExportStage',
]


class ModelConfig:
    extra = 'forbid'
    validate_all = False
    validate_assignment = True
    allow_population_by_field_name = True


class ExportModel(BaseModel):

    class Config(ModelConfig):
        ...


class ModInfo(BaseModel):
    id: str = Field(
        ...,
        title="Mod ID",
    )
    tag: str = Field(
        ...,
        title="Blueprint tag",
        description="Used in place of the mod ID in blueprint paths",
    )
    title: str = Field(
        ...,
        title="Mod name",
    )


class ExportFileModel(ExportModel):
    version: str = Field(
        ...,
        description="Data version of the format <gamemajor>.<gameminor>.<specificversion>, e.g. '306.83.4740398'",
    )
    format: str = Field(
        ...,
        description="Free-form format identifier, changed only when incompatibilities are introduced",
    )
    mod: Optional[ModInfo] = Field(
        None,
        title="Mod info",
        description="Source module information",
    )

    class Config:
        schema_extra = {'$schema': 'http://json-schema.org/draft-07/schema#'}


class JsonHierarchyExportStage(ExportStage, metaclass=ABCMeta):
    gathered_results: Optional[List[Any]]
    '''
    An intermediate helper class that performs hierarchy discovery for core/mods,
    calls the user's `extract_class` for each of them and handles saving the results.
    '''

    @abstractmethod
    def get_format_version(self) -> str:
        '''Return the a format version identifier.'''
        ...

    def get_field(self) -> str:
        '''Return the name to be used as the top-level container in the output JSON.'''
        return self.get_name()

    @abstractmethod
    def get_use_pretty(self) -> bool:
        '''Return True if the file should be prettified, or False if it should be minified.'''
        ...

    @abstractmethod
    def get_ue_type(self) -> str:
        '''Return the fullname of the UE type to gather.'''
        ...

    def get_core_file_path(self) -> PurePosixPath:
        '''Return the relative path of the core output file that should be generated.'''
        name = self.get_name()
        return PurePosixPath(f'{name}.json')

    def get_mod_file_path(self, modid: str) -> PurePosixPath:
        '''Return the relative path of the expected mod output file that should be generated.'''
        name = self.get_name()
        mod_data = self.manager.arkman.getModData(modid)
        assert mod_data
        return PurePosixPath(f'{modid}-{mod_data["name"]}/{name}.json')

    def get_schema_model(self) -> Optional[Type[ExportFileModel]]:
        '''To supply a schema for this export supply a customised Pydantic model type.'''
        return None

    def get_schema_filename(self):
        '''Override to change the name of the generated schema file.'''
        return self.get_core_file_path()

    def pre_load_filter(self, cls_name: str) -> bool:
        '''
        Return True if this class should be included in the data.
        This filter is checked before the asset is loaded and should be light and fast.
        '''
        return True

    @abstractmethod
    def extract(self, proxy: UEProxyStructure) -> Any:
        '''Perform extraction on the given proxy and return any JSON-able object.'''
        raise NotImplementedError

    def get_pre_data(self, modid: Optional[str]) -> Optional[Dict[str, Any]]:  # pylint: disable=unused-argument
        '''
        Return any extra dict entries that should be put *before* the main entries.
        The precense or absence of pre-data *is not* considered when deciding if a file should be saved,
        thus pre-data should be used for metadata only.
        Default behaviour is to include the mod's metadata if extracting for a mod.
        '''
        if modid:
            mod_data = self.manager.arkman.getModData(modid)
            assert mod_data
            title = mod_data['title'] or mod_data['name']
            return dict(mod=dict(id=modid, tag=mod_data['name'], title=title))

        return dict()

    def get_post_data(self, modid: Optional[str]) -> Optional[Dict[str, Any]]:  # pylint: disable=unused-argument
        '''
        Return any extra dict entries that should be put *after* the main entries.
        If any post-data is present it will stop the file being considered empty and avoid it being removed.
        Has access to results gathered from `extract` in `self.gathered_results`.
        '''
        ...

    def extract_core(self, path: Path):
        # Prepare a schema, if requested
        schema_file: Optional[PurePosixPath] = None
        schema_model = self.get_schema_model()  # pylint: disable=assignment-from-none # stupid pylint
        if schema_model:
            schema_file = PurePosixPath('.schema', self.get_schema_filename())
            _output_schema(schema_model, path / schema_file)

        # Core versions are based on the game version and build number
        version = createExportVersion(self.manager.arkman.getGameVersion(), self.manager.arkman.getGameBuildId())  # type: ignore

        filename = self.get_core_file_path()
        proxy_iter = self.manager.iterate_core_exports_of_type(self.get_ue_type(), filter=self.pre_load_filter)
        self._extract_and_save(version, None, path, filename, proxy_iter, schema_file=schema_file)

    def extract_mod(self, path: Path, modid: str):
        # Re-use the core's schema, if existing
        schema_file: Optional[PurePosixPath] = None
        schema_model = self.get_schema_model()  # pylint: disable=assignment-from-none # stupid pylint
        if schema_model:
            schema_file = PurePosixPath('.schema', self.get_schema_filename())

        # Mod versions are based on the game version and mod change date
        version = createExportVersion(self.manager.arkman.getGameVersion(), self.manager.get_mod_version(modid))  # type: ignore

        filename = self.get_mod_file_path(modid)
        proxy_iter = self.manager.iterate_mod_exports_of_type(self.get_ue_type(), modid, filter=self.pre_load_filter)
        self._extract_and_save(version, modid, path, filename, proxy_iter, schema_file=schema_file)

    def _extract_and_save(self,
                          version: str,
                          modid: Optional[str],
                          base_path: Path,
                          relative_path: PurePosixPath,
                          proxy_iter: Iterator[UEProxyStructure],
                          *,
                          schema_file: Optional[PurePosixPath] = None):
        # Work out the output path (cleaned)
        clean_relative_path = PurePosixPath(*(get_valid_filename(p) for p in relative_path.parts))
        output_path = Path(base_path / clean_relative_path)

        # Setup the output structure
        results: List[Any] = []
        format_version = self.get_format_version()
        output: Dict[str, Any] = dict()
        if schema_file:
            model = self.get_schema_model()  # pylint: disable=assignment-from-none # stupid pylint
            assert model
            expected_subtype = _get_model_list_field_type(model, self.get_field())
            output['$schema'] = str(_calculate_relative_path(clean_relative_path, schema_file))
        output['version'] = version
        output['format'] = format_version

        # Pre-data comes before the main items
        pre_data = self.get_pre_data(modid) or dict()
        pre_data = sanitise_output(pre_data)
        output.update(pre_data)

        # Main items array
        output[self.get_field()] = results

        # Do the actual export into the existing `results` list
        for proxy in proxy_iter:
            item_output = self.extract(proxy)
            if item_output:
                if schema_file and expected_subtype and not isinstance(item_output, expected_subtype):
                    raise TypeError(f"Expected {expected_subtype} from schema-enabled exported item but got {type(item_output)}")

                item_output = sanitise_output(item_output)
                results.append(item_output)

        # Make the results available to get_post_data
        self.gathered_results = results

        # Post-data comes after the main items
        post_data = self.get_post_data(modid) or {}
        post_data = sanitise_output(post_data)
        output.update(post_data)
        post_data_has_content = post_data and any(post_data.values())

        # Clear gathered data reference
        del self.gathered_results

        # Save if the data changed
        if results or post_data_has_content:
            save_json_if_changed(output, output_path, self.get_use_pretty())
        else:
            # ...but remove an existing one if the output was empty
            if output_path.is_file():
                output_path.unlink()


def _get_model_field_type(model_type: Type[BaseModel], field_name: str) -> Optional[Type[BaseModel]]:
    '''Pydantic shenanigans to get the type of a model's non-container field.

    >>> class Container(BaseModel):
    ...     plain: str
    ...     list: List[str]
    >>> _get_model_field_type(Container, 'plain') == str
    True
    >>> _get_model_field_type(Container, 'list') == List[str]
    True
    '''
    field = model_type.__fields__.get(field_name, None)
    if not field:
        return None

    outer_type = field.outer_type_
    return outer_type


def _get_model_list_field_type(model_type: Type[BaseModel], field_name: str) -> Optional[Type[BaseModel]]:
    '''Pydantic shenanigans to get the inner type of a model's list field.

    >>> class Container(BaseModel):
    ...     plain: str
    ...     list: List[str]
    >>> _get_model_list_field_type(Container, 'list') == str
    True
    >>> _get_model_list_field_type(Container, 'plain')
    Traceback (most recent call last):
    ...
    TypeError: Expected field `plain` to be List[str] but it was str
    '''
    field = model_type.__fields__.get(field_name, None)
    if not field:
        return None

    outer_type = field.outer_type_
    inner_type = field.type_
    if outer_type != List[inner_type]:  # type: ignore
        raise TypeError(f"Expected field `{field_name}` to be List[{inner_type.__name__}] but it was {outer_type.__name__}")
    return inner_type


def _calculate_relative_path(origin: PurePosixPath, target: PurePosixPath):
    '''
    >>> _calculate_relative_path(PurePosixPath('input.json'), PurePosixPath('.schema', 'output.json'))
    PurePosixPath('.schema/output.json')
    >>> _calculate_relative_path(PurePosixPath('sub','input.json'), PurePosixPath('.schema', 'output.json'))
    PurePosixPath('../.schema/output.json')
    '''
    while True:
        origin = origin.parent

        try:
            result = target.relative_to(origin)
            return result
        except ValueError:
            pass

        if origin == PurePosixPath('.'):
            raise ValueError("Unable to calculate relative path")

        target = PurePosixPath('..', target)


def _output_schema(model_type: Type[BaseModel], path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    schema = model_type.schema_json(by_alias=True, indent='\t')
    with open(path, 'wt', encoding='utf-8', newline='\n') as f:
        f.write(schema)
