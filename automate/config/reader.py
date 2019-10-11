from configparser import ConfigParser

from .sections import *
from .util_types import ModIdAccess

SIMPLE_SECTION_TYPES = {
    'settings': SettingsSection,
    'steamcmd': SteamCmdSection,
    'git': GitSection,
    'errors': ErrorsSection,
    'export-defaults': ExportDefaultsSection,
    'optimisation': OptimisationSection,
}

# These sections gain defaults from the `export-defaults` section
EXPORT_SECTION_TYPES = {
    'export-asb': ExportASBSection,
    'export-wiki': ExportWikiSection,
}


def read_config(filename: str):
    parser = ConfigParser(inline_comment_prefixes='#;')
    parser.optionxform = lambda v: v  # type: ignore # keep exact case of mod names, please
    parser.read(filename)

    # Sections that require special handling
    maps = list(parser['maps'].values())
    mods = list(parser['mods'].keys())
    official_mods = ModIdAccess(parser['official-mods'], keyed_by_id=False)  # type: ignore  # ConfigParser is terribly typed

    # Gather all the simple sections
    simple_sections = {key: kls(**parser[key]) for key, kls in SIMPLE_SECTION_TYPES.items()}

    # Gather all the export sections, applying export_defaults first
    export_defaults = simple_sections['export-defaults'].dict()
    export_sections = {key: kls(**{**export_defaults, **parser[key]}) for key, kls in EXPORT_SECTION_TYPES.items()}

    # Combine all sections
    combined_sections = {
        'maps': maps,
        'mods': mods,
        'official-mods': official_mods,
        **simple_sections,
        **export_sections,
    }

    # Populate the top-level config object
    config = ConfigFile(**combined_sections)
    return config


if __name__ == '__main__':
    read_config('config/config.ini')
