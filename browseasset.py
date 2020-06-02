import os
import sys
from pathlib import Path, PurePosixPath
from tkinter import EventType, Tk, ttk  # type: ignore
from typing import Any, Dict, Optional

from automate.ark import ArkSteamManager
from config import get_global_config
from ue.base import UEBase
from ue.loader import AssetNotFound

root: Optional[Tk] = None
tree: Optional[ttk.Treeview] = None
treenodes: Dict[str, Any] = {}

LEAF_TYPES = (
    'str',
    'StringProperty',
    'Guid',
)


def create_ui():
    global root, tree  # pylint: disable=global-statement

    # Window
    root = Tk()
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    root.minsize(width=600, height=400)
    root.geometry('1100x900')

    # Grid-based layout frame
    frame = ttk.Frame(root, padding="6 6 6 6")
    frame.grid(column=0, row=0, sticky='nsew')
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(0, weight=1)

    # The tree view
    tree = ttk.Treeview(frame, columns=('type', 'value'))
    tree.grid(column=0, row=0, sticky='nsew')
    tree.columnconfigure(0, weight=1)
    tree.rowconfigure(0, weight=1)
    tree.column('#0', width=260, stretch=0)
    tree.heading('type', text='Type')
    tree.heading('value', text='Value')
    tree.column('type', width=110, stretch=False, anchor='e')
    tree.column('value', anchor='w')

    # Styles for some different types
    # https://lospec.com/palette-list/island-joy-16
    tree.tag_configure('int', foreground='#cb4d68')
    tree.tag_configure('bool', foreground='#393457')
    tree.tag_configure('Guid', foreground='#1e8875')
    tree.tag_configure('NameIndex', foreground='#11adc1')
    tree.tag_configure('StringProperty', foreground='#11adc1')
    tree.tag_configure('Property', foreground='#393457')

    # Support virtual tree items with the 'placeholdered' tag
    tree.tag_bind('placeholdered', '<<TreeviewOpen>>', on_tree_open)

    # Scroll bar to control the treeview
    vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    vsb.grid(row=0, column=1, sticky='nse')
    tree.configure(yscrollcommand=vsb.set)


def on_tree_open(evt: EventType):
    assert tree

    # This is called when a node containing a placeholder is opened for the first time
    itemId = tree.selection()[0]
    # node = treenodes[itemId]

    # Remove the placeholder item under this item
    tree.delete(itemId + '_placeholder')

    # Remove placeholdered tag
    tags = tree.item(itemId)['tags']
    tags.remove('placeholdered')
    tree.item(itemId, tags=tags)

    # Convert and insert the proper nodes
    insert_fields_for_node(itemId)


def node_id(node, parentId=None):
    '''Create a string ID for a node.'''
    if isinstance(node, UEBase):
        newId = str(id(node))
        if parentId:
            return parentId + '_' + newId
        return newId
    return None


def type_name(value):
    '''Return the type of a value as a string.'''
    return str(type(value).__name__)


def has_children(value):
    valueType = type_name(value)
    if valueType in LEAF_TYPES:
        return False
    if isinstance(value, UEBase) or type(value) == list:  # isinstance(value, Iterable)
        return True
    return False


def get_node_iterator(node):
    if isinstance(node, list):
        return ((f'0x{i:X} ({i})', value) for i, value in enumerate(node))
    if isinstance(node, UEBase):
        return ((name, node.field_values[name]) for name in getattr(node, 'field_order', None) or node.field_values.keys())
    raise TypeError("Invalid node type for iterator")


def add_placeholder_node(itemId):
    # Add a tag to specifiy this node as having a placeholder (so it will raise an event when opened)
    tags = tree.item(itemId)['tags']
    if not hasattr(tags, 'append'):
        tags = [tags]
    tags.append('placeholdered')
    tree.item(itemId, tags=tags)

    # Add a dummy node to it so it look slike it can be opened
    placeholderId = tree.insert(itemId, 'end', itemId + '_placeholder', text='<virtual tree placeholder>')
    return placeholderId


def add_asset_to_root(asset):
    itemId = tree.insert('', 'end', node_id(asset), text=asset.name, values=(type_name(asset), ))
    treenodes[itemId] = asset
    insert_fields_for_node(itemId)
    tree.item(itemId, open=True)


def get_value_as_string(value):
    if isinstance(value, list):
        return f'{len(value)} entries'
    if isinstance(value, type):
        return value.__name__
    return str(value)


def insert_fields_for_node(parentId):
    node = treenodes[parentId]
    skip_level_name = getattr(node, 'skip_level_field', None)
    if skip_level_name:
        node = node.field_values.get(skip_level_name, node)
    fields = get_node_iterator(node)
    for name, value in fields:
        typeName = str(type(value).__name__)
        newId = node_id(value, parentId)
        strValue = get_value_as_string(value)
        itemId = tree.insert(parentId, 'end', newId, text=name, values=(typeName, strValue), tags=(typeName, ))
        if has_children(value):
            treenodes[itemId] = value
            add_placeholder_node(itemId)


def load_asset(assetname):
    assetname = loader.clean_asset_name(assetname)
    root.title("Asset Browser : " + assetname)
    asset = loader[assetname]
    add_asset_to_root(asset)


def relative_path(path, root):
    try:
        return Path(path).relative_to(root)
    except ValueError:
        return None


def find_asset(assetname, loader):
    if not assetname:
        from tkinter import filedialog
        assetname = filedialog.askopenfilename(title='Select asset file...',
                                               filetypes=(('uasset files', '*.uasset'), ("All files", "*.*")),
                                               initialdir=loader.asset_path)
        assert assetname

    # Attempt to work around MingW hijacking /Game as a root path
    if assetname.startswith('//'):
        assetname = assetname[1:]
    if 'MINGW_PREFIX' in os.environ:
        mingw_base = Path(os.environ['MINGW_PREFIX']).parent
        try:
            path = Path(assetname).relative_to(mingw_base)
            assetname = str(PurePosixPath(path))
        except ValueError:
            pass

    # Try it as-is first
    try:
        clean_path = loader.clean_asset_name(assetname)
        asset = loader[clean_path]
        return asset.assetname
    except Exception:  # pylint: disable=broad-except
        pass

    # Try a combination of possible roots
    asset_path_options = (
        Path(assetname),
        Path(assetname).absolute(),
        Path(assetname).resolve(),
    )

    search_paths = (
        '.',
        Path(get_global_config().settings.DataDir / 'game/ShooterGame'),
        loader.asset_path,
        loader.absolute_asset_path,
    )

    for asset_path in asset_path_options:
        for search_path in search_paths:
            clean_path = relative_path(asset_path, search_path)
            if not clean_path:
                continue

            clean_path = clean_path.with_suffix('')
            assetname = str(PurePosixPath(clean_path))

            try:
                asset = loader[assetname]
                return asset.assetname
            except AssetNotFound:
                continue

    print(f'Not found: {assetname}', file=sys.stderr)
    sys.exit(404)


if __name__ == '__main__':
    arkman = ArkSteamManager()
    loader = arkman.getLoader()
    config = get_global_config()

    assetname = sys.argv[1] if len(sys.argv) > 1 else None
    create_ui()
    assert root

    assetname = find_asset(assetname, loader)
    load_asset(assetname)

    root.mainloop()
