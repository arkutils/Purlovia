from ue.asset import UAsset


def findComponentExports(asset):
    '''Find the main export components from the given asset.'''
    for export in asset.exports.values:
        if str(export.name).startswith('Default__'):
            yield export


def findParentPackage(export):
    '''Find the source asset of the given export.'''
    empty = dict(value=None)

    namespace = export.field_values.get('namespace', empty).value
    if namespace:
        # print(f'ns = {namespace} ({type(namespace)}')
        return str(namespace.name)

    super = export.field_values.get('super', empty).value
    if super:
        # print(f'super = {super} ({type(super)}')
        return findParentPackage(super)

    klass = export.field_values.get('klass', empty).value
    if klass:
        # print(f'klass = {klass} ({type(klass)}')
        return findParentPackage(klass)


def findDependencies(asset):
    '''Find the names of all relevant assets this asset depends on.'''
    # Packages of classes of main components
    for component in findComponentExports(asset):
        # print(f'component: {component.name}')
        yield findParentPackage(component.klass.value)

    # Packages of classes of sub-components
    for subcomponent in findSubComponents(asset):
        # print(f'sub-component: {subcomponent.name}')
        yield findParentPackage(subcomponent.klass.value)


def findSubComponents(asset, expectedklassname='BlueprintGeneratedClass'):
    '''Find sub-components that are used within this asset asset.'''
    for export in asset.exports.values:
        kls = export.klass and export.klass.value
        klskls = kls and kls.klass.value
        if not klskls: continue
        if str(klskls) == expectedklassname:
            yield export
