import sys
from tkinter import *
from tkinter import ttk
from collections.abc import Iterable

from stream import MemoryStream
from ue.base import UEBase
from ue.asset import UAsset
import loader

root = None
tree = None
treenodes = {}

LEAF_TYPES = (
    'str',
    'StringProperty',
    'Guid',
)


def create_ui():
    global root,tree

    # Window
    root = Tk()
    root.title("Asset Browser")
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    root.minsize(width=600, height=400)
    root.geometry('800x900')

    # Grid-based layout frame
    frame = ttk.Frame(root, padding="6 6 6 6")
    frame.grid(column=0, row=0, sticky=(N, W, E, S))
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(0, weight=1)

    # The tree view
    tree = ttk.Treeview(frame, columns=('type', 'value')) # , selectmode='none'
    tree.grid(column=0, row=0, sticky=(N, W, E, S))
    tree.columnconfigure(0, weight=1)
    tree.rowconfigure(0, weight=1)
    tree.heading('type', text='Type')
    tree.heading('value', text='Value')
    tree.column('type', width=90, stretch=False, anchor='e')
    tree.column('value', anchor='w')

    # Support virtual tree items with the 'placeholdered' tag
    # tree.tag_configure('placeholdered', foreground='#808080')
    tree.tag_bind('placeholdered', '<<TreeviewOpen>>', on_tree_open)

    # Scroll bar to control the treeview
    vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    vsb.grid(row=0, column=1, sticky='nse')
    tree.configure(yscrollcommand=vsb.set)


def on_tree_open(evt: EventType):
    # This is called when a node containing a placeholder is opened for the first time
    itemId = tree.selection()[0]
    node = treenodes[itemId]

    # Remove the placeholder item under this item
    tree.delete(itemId + '_placeholder')

    # Remove placeholdered tag
    tags = tree.item(itemId)['tags']
    tags.remove('placeholdered')
    tree.item(itemId, tags=tags)

    # Convert and insert the proper nodes
    insert_fields_for_node(itemId)


def node_id(node, parentId=None):
    if isinstance(node, UEBase):
        newId = str(id(node))
        if parentId:
            return parentId + '_' + newId
        return newId
    return None


def type_name(value):
    return str(type(value).__name__)


def has_children(value):
    valueType = type_name(value)
    if valueType in LEAF_TYPES:
        return False
    if isinstance(value, UEBase) or type(value) == list: # isinstance(value, Iterable)
        return True
    return False


def get_node_iterator(node):
    if isinstance(node, list):
        return ( (f'0x{i:X} ({i})', value) for i,value in enumerate(node) )
    if isinstance(node, UEBase):
        return ( (name,node.field_values[name]) for name in getattr(node, 'field_order', None) or node.field_values.keys() )
    raise TypeError("Invalid node type for iterator")


def add_placeholder_node(itemId):
    # dummy node added to anythng that should be able to open, before it's contents have been inserted
    tree.item(itemId, tags=('placeholdered', ))
    placeholderId = tree.insert(itemId, 'end', itemId + '_placeholder', text='<virtual tree placeholder>')


def add_asset_to_root(asset):
    itemId = tree.insert('', 'end', node_id(asset), text=asset.name, values=(type_name(asset), ))
    treenodes[itemId] = asset
    add_placeholder_node(itemId)


def insert_fields_for_node(parentId):
    node = treenodes[parentId]
    fields = get_node_iterator(node)
    for name,value in fields:
        typeName = str(type(value).__name__)
        newId =  node_id(value, parentId)
        itemId = tree.insert(parentId, 'end', newId, text=name, values=(typeName, str(value)))
        if has_children(value):
            treenodes[itemId] = value
            add_placeholder_node(itemId)


def load_asset(assetname):
    filename = loader.convert_asset_name_to_path(assetname)
    mem = loader.load_raw_asset_from_file(filename)
    stream = MemoryStream(mem, 0, len(mem))
    asset = UAsset(stream)
    asset.name = assetname.split('/')[-1]
    asset.deserialise()
    asset.link()

    add_asset_to_root(asset)

create_ui()
assetname = sys.argv[1] if len(sys.argv)>1 else '/Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP_Argent'
load_asset(assetname)
root.mainloop()
