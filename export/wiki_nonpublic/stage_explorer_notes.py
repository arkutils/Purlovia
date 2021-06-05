from typing import Any, Dict, List, Optional, cast

from ark.types import PrimalGameData
from automate.hierarchy_exporter import ExportModel, Field
from ue.loader import AssetLoadException
from ue.proxy import UEProxyStructure
from ue.utils import get_leaf_from_assetname
from utils.log import get_logger

from .single_asset_stage import SingleAssetExportStage

logger = get_logger(__name__)

__all__ = [
    'ExplorerNotesStage',
]


class AudioEntry(ExportModel):
    bp: str
    transcript: str


class ExplorerNote(ExportModel):
    author: str
    name: str
    authorIcon: Optional[str] = None
    image: Optional[str] = None
    creatureTag: str = Field('None', description="Name tag of a creature this dossier is for.")
    transcript: Optional[str] = None
    audio: Optional[Dict[str, AudioEntry]] = None


EXPLORER_NOTE_TYPE_MAP = {
    0: 'Helena',
    1: 'Rockwell',
    2: 'Mei Yin',
    3: 'Nerva',
    4: 'Bossier',
    6: 'Raia',
    7: 'Dahkeya',
    8: 'Grad Student',
    9: 'Diana',
    10: 'The One Who Waits',
    11: 'Santiago',
    12: 'HLN-A',
    13: 'Nida',
    14: 'Gabriel',
}

GAME_VO_LANGUAGES = ('en', 'de', 'es', 'fe', 'it', 'jp', 'pt', 'ru', 'zh')
GAME_VO_FOLDERS = ('English', 'German', 'Spanish', 'French', 'Italian', 'Japanese', 'Portuguese', 'Russian', 'Mandarin')


class ExplorerNotesStage(SingleAssetExportStage):
    def get_name(self) -> str:
        return 'explorer_notes'

    def get_asset_name(self) -> str:
        '''Return the fullname of the asset to load.'''
        return '/Game/PrimalEarth/CoreBlueprints/COREMEDIA_PrimalGameData_BP'

    def get_use_pretty(self) -> bool:
        return bool(self.manager.config.export_wiki.PrettyJson)

    def get_format_version(self):
        return "1"

    def extract(self, proxy: UEProxyStructure) -> Optional[Dict[str, Any]]:
        pgd = cast(PrimalGameData, proxy)
        results: List[ExplorerNote] = []

        for entry in pgd.ExplorerNoteEntries[0]:
            d = entry.as_dict()
            type_id = int(d['ExplorerNoteType'])

            # Retrieve the path to the author icon reference.
            icon_ref = d['ExplorerNoteIconMaterial']
            icon = None
            if icon_ref and icon_ref.value and icon_ref.value.value:
                icon = icon_ref.value.value.fullname
            else:
                icon_ref = d['ExplorerNoteIcon']
                if icon_ref and icon_ref.value and icon_ref.value.value:
                    icon = icon_ref.value.value.fullname

            # Retrieve the note's texture path.
            texture_ref = d['ExplorerNoteTexture']
            texture = None
            if texture_ref and texture_ref.values[0]:
                texture = str(texture_ref.values[0])

            # Retrieve text/subtitles.
            audio = d['LocalizedAudio'].values
            text = None
            audio_info = None
            if not audio:
                # Classic text note.
                text = str(d['LocalizedSubtitle'])
            else:
                # Audio note.
                # Retrieve all directly linked sound cue paths.
                waves = dict()
                for struct in audio:
                    s = struct.as_dict()
                    iso_code = str(s['TwoLetterISOLanguageName'])
                    cue = s['LocalizedSoundCue'].values[0].value
                    result = get_sound_wave_path_from_cue(self.manager.loader, cue)
                    if result:
                        waves[iso_code] = result

                # Retrieve all runtime discovered sound cue paths.
                base_path: str = waves['en']
                if '/English/' in base_path:
                    base_path = base_path[:base_path.rindex('/English/')]
                    base_name = get_leaf_from_assetname(waves['en'])
                    base_name = base_name[:-2]
                    for index, iso_code in enumerate(GAME_VO_LANGUAGES):
                        if iso_code in waves:
                            continue

                        sw_path = base_path + '/' + GAME_VO_FOLDERS[index] + '/' + base_name + iso_code
                        try:
                            self.manager.loader[sw_path]
                            waves[iso_code] = sw_path
                        except AssetLoadException:
                            continue

                # Retrieve all subtitles.
                audio_info = dict()
                for iso_code, ref in waves.items():
                    audio_result = gather_data_from_sound_wave(self.manager.loader, ref)
                    if audio_result:
                        audio_info[iso_code] = audio_result

            results.append(
                ExplorerNote(
                    author=EXPLORER_NOTE_TYPE_MAP.get(type_id, type_id),
                    name=str(d['ExplorerNoteDescription']),
                    authorIcon=icon,
                    image=texture,
                    creatureTag=str(d['DossierTameableDinoNameTag']),
                    transcript=text,
                    audio=audio_info,
                ))

        return dict(notes=results)


def get_sound_wave_path_from_cue(loader, cue_ref: str) -> Optional[str]:
    # Check if cue reference is valid.
    if not cue_ref:
        return None

    # Load the asset.
    cue_asset = loader[cue_ref]
    cue_export = cue_asset.default_export
    if not cue_export:
        return None

    for export in cue_asset.exports:
        clsname = export.klass.value.fullname
        if clsname == '/Script/Engine.SoundNodeWavePlayer':
            sw = export.properties.get_property('SoundWave', fallback=None)
            if sw:
                return sw.value.value.fullname

    return None


def gather_data_from_sound_wave(loader, ref: str) -> Optional[AudioEntry]:
    # Check if cue reference is valid.
    if not ref:
        return None

    # Load the asset.
    asset = loader[ref]
    export = asset.default_export
    if not export:
        return None

    # Retrieve subtitles.
    subtitles = export.properties.get_property('SpokenText', fallback=None)
    if not subtitles:
        return None

    return AudioEntry(bp=ref, transcript=subtitles.value)
