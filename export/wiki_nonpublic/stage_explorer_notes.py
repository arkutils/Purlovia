from typing import Any, Dict, List, Optional, cast

from ark.types import PrimalGameData
from automate.hierarchy_exporter import ExportModel, Field
from ue.proxy import UEProxyStructure
from utils.log import get_logger

from .single_asset_stage import SingleAssetExportStage

logger = get_logger(__name__)

__all__ = [
    'ExplorerNotesStage',
]


class ExplorerNote(ExportModel):
    author: str
    name: str
    authorIcon: Optional[str] = None
    image: Optional[str] = None
    creatureTag: str = Field('None', description="Name tag of a creature this dossier is for.")
    transcript: str
    alternativeTranscripts: Optional[Dict[str, str]] = None


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
}


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

            # Retrieve text.
            audio = d['LocalizedAudio'].values
            if not audio:
                text = str(d['LocalizedSubtitle'])
            else:
                text = ''
                # decode_note_audio_sets(loader, audio)

            results.append(
                ExplorerNote(
                    author=EXPLORER_NOTE_TYPE_MAP.get(type_id, type_id),
                    name=str(d['ExplorerNoteDescription']),
                    authorIcon=icon,
                    image=texture,
                    creatureTag=str(d['DossierTameableDinoNameTag']),
                    transcript=text,
                ))

        return dict(notes=results)
