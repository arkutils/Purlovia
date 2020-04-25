import pytest

from .testutils import *


@pytest.mark.uses_copyright_material
def test_Guid_DinoColorSet_Baryonyx():
    asset = load_asset('PrimalEarth/CoreBlueprints/DinoColorSet_Baryonyx')
    prop = asset.exports[4].properties[5]
    assert str(prop.header.name) == 'BlueprintGuid'
    assert len(prop.value.values) == 1
    entry = prop.value.values[0]
    assert isinstance(entry, Guid)
    assert str(entry) == '99b635ca-c7d1-4673-8398-69cde8efb9ee'
