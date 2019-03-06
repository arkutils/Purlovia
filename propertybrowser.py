import sys
from tkinter import Tk
from tkinter import ttk, filedialog
from collections.abc import Iterable
from collections import defaultdict

from stream import MemoryStream
from ue.base import UEBase
from ue.asset import UAsset
from ue.properties import Property, FloatProperty, StructProperty
import loader

root = None
tree = None

assetlist = []

# propertyvalues[propname][assetname] = value
propertyvalues = defaultdict(lambda: defaultdict(lambda: None))


def create_ui():
    global root, tree

    # Window
    root = Tk()
    root.title("Property Browser : " + mainasset)
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    root.minsize(width=600, height=400)
    root.geometry('1000x800')

    # Grid-based layout frame
    frame = ttk.Frame(root, padding="6 6 6 6")
    frame.grid(column=0, row=0, sticky='nsew')
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(0, weight=1)

    # The tree view
    tree = ttk.Treeview(frame, columns=assetlist)
    tree.grid(column=0, row=0, sticky='nsew')
    tree.columnconfigure(0, weight=1)
    tree.rowconfigure(0, weight=1)
    tree.column('#0', stretch=0, width=340)
    for i, assetname in enumerate(assetlist):
        smallname = assetname.replace('DinoCharacterStatusComponent', 'DCSC').replace('Character', 'Chr')
        tree.heading(i, text=smallname)
        tree.column(i, anchor='w')

    # Scroll bar to control the treeview
    vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    vsb.grid(row=0, column=1, sticky='nse')
    tree.configure(yscrollcommand=vsb.set)


def type_name(value):
    '''Retuen the type of a value as a string.'''
    return str(type(value).__name__)


def get_value_as_string(value):
    if isinstance(value, list): return f'{len(value)} entries'
    if isinstance(value, type): return value.__name__
    if isinstance(value, StructProperty): return '<struct>'
    if isinstance(value, Property) or hasattr(value, 'value'): return get_value_as_string(value.value)
    if isinstance(value, FloatProperty): return value.rounded
    if value is None: return ''
    return str(value)


def load_asset(assetname):
    assetname = loader.clean_asset_name(assetname)
    print('Loading:', assetname)

    filename = loader.convert_asset_name_to_path(assetname)
    mem = loader.load_raw_asset_from_file(filename)
    stream = MemoryStream(mem, 0, len(mem))
    asset = UAsset(stream)
    asset.name = assetname.split('/')[-1]
    asset.deserialise()
    asset.link()

    small_assetname = assetname.split('/')[-1]

    # Look for the default export and record its properties
    default_export = asset.findDefaultExport()
    if not default_export: return
    record_properties(default_export.properties, small_assetname)

    # Load the parent asset, if we have one
    parent_pkg = asset.findParentPackageForExport(default_export)
    if parent_pkg and parent_pkg.strip('/').startswith('Game'):
        load_asset(parent_pkg)


def should_filter_out(prop):
    proptype = str(prop.header.type)
    if proptype == 'StructProperty': return True
    if proptype == 'ArrayProperty': return True
    if proptype == 'ObjectProperty': return True


def record_properties(properties, assetname):
    assetlist.append(assetname)
    for prop in properties:
        if should_filter_out(prop): continue
        propname = f'{prop.header.name}[{prop.header.index}]'
        value = get_value_as_string(prop)
        propertyvalues[propname][assetname] = value


def fill_property_grid():
    for propname, propvalues in propertyvalues.items():
        assetvalues = [propvalues[assetname] or '' for assetname in assetlist]
        tree.insert('', 'end', text=propname, values=assetvalues)


mainasset = sys.argv[1] if len(sys.argv) > 1 else '/Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP_Argent'
load_asset(mainasset)
create_ui()
fill_property_grid()
root.mainloop()
