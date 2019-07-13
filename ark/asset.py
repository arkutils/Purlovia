from typing import *

from ue.asset import UAsset, ExportTableItem


def findComponentExports(asset: UAsset) -> Iterator[ExportTableItem]:
    '''Find the main export components from the given asset.'''
    for export in asset.exports.values:
        if str(export.name).startswith('Default__'):
            yield export


def findSubComponentExports(asset: UAsset, expectedklassname='BlueprintGeneratedClass') -> Iterator[ExportTableItem]:
    '''Find sub-components that are used within this asset.'''
    for export in asset.exports.values:
        kls = export.klass and export.klass.value
        klskls = kls and kls.klass.value
        if export.namespace.value == asset.default_export:
            yield export
        elif klskls and str(klskls) == expectedklassname:
            yield export


def findParentPackages(asset: UAsset) -> Iterator[str]:
    '''Find the parents of the main export components from the given asset.'''
    for export in findComponentExports(asset):
        pkg = findExportSourcePackage(export)  #.klass.value ???
        if pkg:
            yield pkg


def findSubComponentParentPackages(asset: UAsset, expectedklassname='BlueprintGeneratedClass') -> Iterator[str]:
    for export in findSubComponentExports(asset, expectedklassname=expectedklassname):
        pkg = findExportSourcePackage(export.klass.value)
        if pkg:
            yield pkg


def findExportSourcePackage(export: ExportTableItem) -> Optional[str]:
    '''Find the source package of the given export.'''
    empty = dict(value=None)

    namespace = export.field_values.get('namespace', empty).value
    if namespace:
        return str(namespace.name)

    super_export = export.field_values.get('super', empty).value
    if super_export:
        return findExportSourcePackage(super_export)

    klass_export = export.field_values.get('klass', empty).value
    if klass_export:
        return findExportSourcePackage(klass_export)

    return None


def findAllDependencies(asset) -> Iterator[str]:
    '''Find which packages this asset components and sub-components depend on.'''
    # Packages of classes of main components
    for parent in findParentPackages(asset):
        yield parent

    # Packages of classes of sub-components
    for subcmpparent in findSubComponentParentPackages(asset):
        yield subcmpparent
