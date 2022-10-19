import sys
from collections import defaultdict
from tkinter import Tk, ttk
from typing import Any, Dict, Optional

import ark.asset
from automate.ark import ArkSteamManager
from ue.loader import AssetNotFound
from ue.paths import find_asset_from_external_path
from ue.properties import FloatProperty, Property, StructProperty

root: Optional[Tk] = None
tree: Optional[ttk.Treeview] = None

assetlist = []

# propertyvalues[propname][index][assetname] = value
propertyvalues: Dict[str, Dict[int, Dict[str, Any]]] = \
    defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: None)  # type: ignore
    ))


def create_ui():
    global root

    # Window
    root = Tk()
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    root.minsize(width=600, height=400)
    root.geometry('1000x800')


def type_name(value):
    '''Return the type of a value as a string.'''
    return str(type(value).__name__)


def get_value_as_string(value):
    if isinstance(value, list):
        return f'{len(value)} entries'
    if isinstance(value, type):
        return value.__name__
    if isinstance(value, StructProperty):
        return '<struct>'
    if isinstance(value, FloatProperty):
        return value.rounded
    if isinstance(value, Property) or hasattr(value, 'value'):
        return get_value_as_string(value.value)
    if value is None:
        return ''
    return str(value)


def find_asset(assetname, loader):
    try:
        assetname = find_asset_from_external_path(assetname, loader, True)
    except AssetNotFound:
        print(f'Not found: {assetname}', file=sys.stderr)
        sys.exit(404)

    return assetname


def load_asset(assetname):
    if not assetname.startswith('/Game'):
        return

    assetname = loader.clean_asset_name(assetname)
    asset = loader[assetname]

    # Take properties and overrides from each sub-component recursively
    for component in ark.asset.findSubComponentExports(asset):
        componentname = ark.asset.findExportSourcePackage(component.klass.value)
        print(f'Sub-Component: {componentname}')
        record_properties(component.properties, '+' + componentname.split('/')[-1])
        load_asset(componentname)

    # Take properties and overrides from each component recursively
    for component in ark.asset.findComponentExports(asset):
        record_properties(component.properties, assetname.split('/')[-1])
        parentpkg = ark.asset.findExportSourcePackage(component)
        print(f'Component: {parentpkg}')
        load_asset(parentpkg)


def should_filter_out(prop):
    proptype = str(prop.header.type)
    if proptype == 'StructProperty':
        return True
    if proptype == 'ArrayProperty':
        return True
    if proptype == 'ObjectProperty':
        return True


def record_properties(properties, assetname):
    if len(properties) < 1:
        return
    assetlist.append(assetname)
    for prop in properties:
        if should_filter_out(prop):
            continue
        value = get_value_as_string(prop)
        propertyvalues[str(prop.header.name)][prop.header.index][assetname] = value


def fill_property_grid():
    global tree

    # Grid-based layout frame
    frame = ttk.Frame(root, padding="6 6 6 6")
    frame.grid(column=0, row=0, sticky='nsew')
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(0, weight=1)

    # The tree view
    tree = ttk.Treeview(frame, columns=['name', 'index'] + assetlist)
    tree.grid(column=0, row=0, sticky='nsew')
    tree.columnconfigure(0, weight=1)
    tree.rowconfigure(0, weight=1)
    tree.column('#0', stretch=0, width=0)
    tree.column('name', stretch=0, width=320, anchor='e')
    tree.column('index', stretch=0, width=36, anchor='c')
    tree.heading('name', text='Name')
    tree.heading('index', text='Index')

    # Simple styling
    tree.tag_configure('odd', background='#e0e0e0')

    # Scroll bar to control the treeview
    vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    vsb.grid(row=0, column=1, sticky='nse')
    tree.configure(yscrollcommand=vsb.set)
    for i, assetname in enumerate(assetlist):
        smallname = assetname.replace('DinoCharacterStatusComponent', 'DCSC').replace('Character', 'Chr').replace('_BP', '')
        tree.heading(i + 2, text=smallname)
        tree.column(i + 2, width=60, stretch=1, anchor='c')

    odd = False
    for propname, propvalues in sorted(propertyvalues.items(), key=lambda p: p[0]):
        for index, values in sorted(propvalues.items(), key=lambda p: p[0]):
            assetvalues = [values[assetname] or '' for assetname in assetlist]
            tree.insert('', 'end', text=propname, values=[propname, index] + assetvalues, tags=('odd' if odd else 'even', ))
            odd = not odd


if __name__ == '__main__':
    arkman = ArkSteamManager()
    loader = arkman.getLoader()

    mainasset = sys.argv[1] if len(sys.argv) > 1 else None
    create_ui()
    assert root

    mainasset = find_asset(mainasset, loader)
    print(f"Asset: {mainasset}")

    root.title(f"Property Browser : {mainasset}")
    load_asset(mainasset)
    fill_property_grid()
    root.mainloop()
