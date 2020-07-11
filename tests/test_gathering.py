import pytest

from ark.gathering import gather_dcsc_properties
from ark.types import PrimalDinoCharacter, PrimalDinoStatusComponent, PrimalGameData
from ue.gathering import gather_properties
from ue.hierarchy import inherits_from
from ue.proxy import UEProxyStructure

from .common import *  # noqa: F401,F403  # needed to pick up all fixtures
from .common import DEINO_CHR, DODO_AB_CHR, DODO_CHR, PTM_DCSC_CONFLICT_CHR, TEST_PGD_CLS, TROODON_CHR, X_DRAGON_CHR, ScanLoadFn

# pylint: disable=singleton-comparison


@pytest.mark.requires_game
def test_gather_purloviatest_pgd(scan_and_load):
    export = scan_and_load(TEST_PGD_CLS)
    pgd: PrimalGameData = gather_properties(export)
    assert isinstance(pgd, UEProxyStructure)
    assert isinstance(pgd, PrimalGameData)

    assert str(pgd.ModName[0]) == 'PurloviaTEST'
    assert str(pgd.ModDescription[0]) == 'Test mod used for Purlovia'


@pytest.mark.requires_game
def test_gather_dodo(scan_and_load):
    dodo = scan_and_load(DODO_CHR)
    dodo_chr: PrimalDinoCharacter = gather_properties(dodo)
    assert isinstance(dodo_chr, UEProxyStructure)
    assert isinstance(dodo_chr, PrimalDinoCharacter)
    assert str(dodo_chr.DescriptiveName[0]) == 'Dodo'


@pytest.mark.requires_game
def test_gather_ab_dodo(scan_and_load):
    dodo_ab = scan_and_load(DODO_AB_CHR)
    assert inherits_from(dodo_ab, DODO_CHR)
    dodo_ab_chr: PrimalDinoCharacter = gather_properties(dodo_ab)
    assert isinstance(dodo_ab_chr, UEProxyStructure)
    assert isinstance(dodo_ab_chr, PrimalDinoCharacter)
    assert str(dodo_ab_chr.DescriptiveName[0]) == 'Aberrant Dodo'


@pytest.mark.requires_game
def test_gather_dodo_dcsc(scan_and_load):
    dodo = scan_and_load(DODO_CHR)
    dodo_dcsc = gather_dcsc_properties(dodo)
    assert isinstance(dodo_dcsc, UEProxyStructure)
    assert isinstance(dodo_dcsc, PrimalDinoStatusComponent)
    assert dodo_dcsc.MaxStatusValues[0] == 40  # only in Dodo chr
    assert dodo_dcsc.MaxStatusValues[3] == 150  # only in DCSC asset
    assert dodo_dcsc.MaxStatusValues[7] == 50  # in DCSC, then overridden by Dodo


@pytest.mark.requires_game
def test_gather_troodon_dcsc(scan_and_load):
    chr_export = scan_and_load(TROODON_CHR)
    props = gather_dcsc_properties(chr_export)
    assert isinstance(props, UEProxyStructure)
    assert isinstance(props, PrimalDinoStatusComponent)
    assert props.MaxStatusValues[0] == 200  # only in Troodon DCSC asset
    assert props.MaxStatusValues[4] == 200  # in Troodon chr asset
    assert props.MaxStatusValues[7] == 140  # in DCSC, overridden in Troodon DCSC


@pytest.mark.requires_game
def test_gather_troodon_dcsc_alt(scan_and_load: ScanLoadFn):
    chr_export = scan_and_load(TROODON_CHR)
    props = gather_dcsc_properties(chr_export, alt=True)
    assert isinstance(props, UEProxyStructure)
    assert isinstance(props, PrimalDinoStatusComponent)
    assert props.MaxStatusValues[0] == 200  # only in Troodon DCSC asset
    assert props.MaxStatusValues[4] == 100  # was 200 in Troodon chr asset, skipped due to alt=True
    assert props.MaxStatusValues[7] == 140  # in DCSC, overridden in Troodon DCSC


@pytest.mark.requires_game
def test_gather_deino(scan_and_load: ScanLoadFn):
    # Deino has a species-specific DCSC with a lower priority than the one it inherits
    chr_export = scan_and_load(DEINO_CHR)
    props = gather_dcsc_properties(chr_export)
    assert isinstance(props, UEProxyStructure)
    assert isinstance(props, PrimalDinoStatusComponent)
    assert props.MaxStatusValues[0] == 200  # from Raptor DCSC because Deino DCSC priority is -1
    assert props.MaxStatusValues[1] == 150  # from Raptor DCSC because Deino DCSC priority is -1
    assert props.MaxStatusValues[3] == 150  # from default DCSC


@pytest.mark.requires_game
def test_gather_dragon_boss(scan_and_load: ScanLoadFn):
    # DragonBoss has two DCSCs, one with a higher priority
    chr_export = scan_and_load(X_DRAGON_CHR)
    props = gather_dcsc_properties(chr_export)
    assert isinstance(props, UEProxyStructure)
    assert isinstance(props, PrimalDinoStatusComponent)
    assert props.bCanSuffocate[0] == False


@pytest.mark.requires_game
def test_gather_x_dragon(scan_and_load: ScanLoadFn):
    # X-Dragon inherits the same two DCSCs from DragonBoss
    chr_export = scan_and_load(X_DRAGON_CHR)
    props = gather_dcsc_properties(chr_export)
    assert isinstance(props, UEProxyStructure)
    assert isinstance(props, PrimalDinoStatusComponent)
    assert props.bCanSuffocate[0] == False


@pytest.mark.requires_game
def test_gather_dcsc_conflict(scan_and_load: ScanLoadFn):
    # Species inherits from Quetz but doesn't use that DCSC
    # Used to verify that DCSCs shouldn't be combined if no override exists for a property
    chr_export = scan_and_load(PTM_DCSC_CONFLICT_CHR)
    props = gather_dcsc_properties(chr_export)
    assert isinstance(props, UEProxyStructure)
    assert isinstance(props, PrimalDinoStatusComponent)
    assert props.MaxStatusValues[0] == 100  # from PTM_DCSC and not DCSC_Quetz (1200)
    assert props.MaxStatusValues[1] == 100  # from PTM_DCSC and not DCSC_Quetz (800)
    assert props.MaxStatusValues[2] == 100  # from PTM_DCSC and not DCSC_Quetz (1850)
    assert props.MaxStatusValues[4] == 100  # from PTM_DCSC and not DCSC_Quetz (1200)
    assert props.TamedBaseHealthMultiplier[0] == 1  # from PTM_DCSC and not DCSC_Quetz (0.85)
