from configparser import ConfigParser
from typing import Optional

from .sections import ConfigFile, DevSection, ErrorsSection, ExportASBSection, ExportDefaultsSection, \
    ExportWikiSection, GitSection, OptimisationSection, ProcessingSection, SettingsSection, SteamCmdSection
from .util_types import ModAliases, ModIdAccess

SIMPLE_SECTION_TYPES = {
    'settings': SettingsSection,
    'dev': DevSection,
    'steamcmd': SteamCmdSection,
    'git': GitSection,
    'errors': ErrorsSection,
    'export-defaults': ExportDefaultsSection,
    'processing': ProcessingSection,
    'optimisation': OptimisationSection,
}

# These sections gain defaults from the `export-defaults` section
EXPORT_SECTION_TYPES = {
    'export-asb': ExportASBSection,
    'export-wiki': ExportWikiSection,
}


def read_config(filename: Optional[str] = None, config_string: Optional[str] = None):
    if filename is None and config_string is None:
        raise ValueError("filename or config string are required")

    parser = ConfigParser(inline_comment_prefixes='#;')
    parser.optionxform = lambda v: v  # type: ignore # keep exact case of mod names, please

    if filename is not None:
        parser.read(filename)
    elif config_string is not None:
        parser.read_string(config_string)

    # Sections that require special handling
    mods = list(parser['mods'].keys())
    official_mods = ModIdAccess(parser['official-mods'], keyed_by_id=False)  # type: ignore  # ConfigParser is terribly typed
    combine_mods = ModAliases(parser['combine-mods'])  # type: ignore  # ConfigParser is terribly typed

    # Gather all the simple sections
    simple_sections = {key: kls(**parser[key]) for key, kls in SIMPLE_SECTION_TYPES.items()}

    # Gather all the export sections, applying export_defaults first
    export_defaults = simple_sections['export-defaults'].dict()
    export_sections = {key: kls(**{**export_defaults, **parser[key]}) for key, kls in EXPORT_SECTION_TYPES.items()}

    # Combine all sections
    combined_sections = {
        'mods': mods,
        'official-mods': official_mods,
        'combine-mods': combine_mods,
        **simple_sections,
        **export_sections,
    }

    # Populate the top-level config object
    config = ConfigFile(**combined_sections)
    return config


if __name__ == '__main__':
    read_config('config/config.ini')
