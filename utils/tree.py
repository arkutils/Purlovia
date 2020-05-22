'''
Reusable tree structure, including a variant with a fast indexed lookup.
'''
from __future__ import annotations

from collections import deque
from typing import Callable, Deque, Dict, Generic, Iterable, List, Optional, TypeVar, Union

try:
    from IPython.lib.pretty import PrettyPrinter  # type: ignore
    support_pretty = True
except ImportError:
    support_pretty = False

__all__ = [
    'Node',
    'IndexedTree',
]

T = TypeVar('T')

MISSING = object()


class Node(Generic[T]):

    def __init__(self, data: T, parent: Optional[Node[T]] = None):
        self._data: T = data
        self._parent: Optional[Node[T]] = parent
        self._nodes: List[Node[T]] = list()

    @property
    def data(self) -> T:
        return self._data

    @property
    def parent(self) -> Optional[Node[T]]:
        return self._parent

    @property
    def parent_data(self) -> Optional[T]:
        return self._parent.data if self._parent else None

    @property
    def nodes(self) -> List[Node[T]]:
        return self._nodes

    def walk_iterator(self, skip_self=True, breadth_first=False) -> Iterable[Node[T]]:
        q: Deque[Node[T]] = deque()
        q.append(self)
        while q:
            node: Node[T] = q.popleft()
            if skip_self:
                skip_self = False
            else:
                yield node

            if breadth_first:
                q.extend(node.nodes)
            else:
                q.extendleft(reversed(node.nodes))

    def walk(self, fn: Callable[[Node[T]], Optional[bool]]) -> Optional[bool]:
        '''
        Call the given function for every node below this one, depth-first.
        Return `False` from `fn` to stop.
        Returns `False` if `fn` ever returned it, else `None`.
        '''
        if fn(self) is False:
            return False

        for node in self.nodes:
            if node.walk(fn) is False:
                return False

        return None

    def add(self, data: Union[T, Node[T]]) -> Node[T]:
        node: Node[T] = data if isinstance(data, Node) else Node[T](data)
        node._parent = self  # pylint: disable=protected-access  # it's our own class
        self._nodes.append(node)
        return node

    def __contains__(self, data: Union[T, Node[T]]):
        if isinstance(data, Node):
            return data in self._nodes
        return any(node.data is data for node in self._nodes)

    def __repr__(self):
        return f'{self.__class__.__name__}({self._data!r})'

    if support_pretty:

        def _repr_pretty_(self, p: PrettyPrinter, cycle: bool):
            if cycle:
                p.text(self.__class__.__name__ + '(<cyclic>)')
                return

            p.pretty(self._data)
            with p.group(4, '', ''):
                for node in self._nodes:
                    p.break_()
                    p.pretty(node)


class IndexedTree(Generic[T]):
    _key_fn: Optional[Callable[[T], str]]
    _lookup: Dict[str, Node[T]]
    root: Node[T]

    def __init__(self, root: T, key_fn: Optional[Callable[[T], str]] = None):
        self._key_fn = key_fn
        self._root_data = root
        self.clear()

    def clear(self):
        self._lookup = dict()
        self.root = Node[T](self._root_data)
        self._register(self.root)

    def add(self, parent: Union[str, Node[T]], data: Union[T, Node[T]]) -> Node[T]:
        parent_node = self._handle_parent_arg(parent)

        if not isinstance(data, Node):
            data = Node[T](data)

        self._register(data)
        parent_node.add(data)

        return data

    def insert_segment(self, parent: Union[str, Node[T]], partial_tree: Node[T]):
        parent_node = self._handle_parent_arg(parent)
        partial_tree.walk(self._register)
        parent_node.add(partial_tree)

    def keys(self) -> Iterable[str]:
        yield from self._lookup.keys()

    def __getitem__(self, key: str) -> Node[T]:
        return self._lookup[key]

    def __contains__(self, key: str) -> bool:
        return key in self._lookup

    def __len__(self) -> int:
        return len(self._lookup)

    def __bool__(self) -> bool:
        return bool(self._lookup)

    def get(self, key: str, fallback=MISSING) -> Node[T]:
        if fallback is MISSING:
            return self._lookup[key]

        return self._lookup.get(key, fallback)

    def ingest_list(self, src: List[T], parent_fn: Callable[[T], Optional[T]]):
        '''
        Add multiple items from a list.
        Each list item must have a parent that is discoverable using the supplied function.
        '''
        for item in src:
            self._ingest(item, parent_fn)

    def _ingest(self, item: T, parent_fn: Callable[[T], Optional[T]]):
        current: T = item
        assert current
        segment: Optional[Node[T]] = None
        key: str = self._key_fn(current) if self._key_fn else current  # type: ignore
        if key in self:
            return

        while True:
            old_segment = segment
            segment = Node(current)
            if old_segment:
                segment.add(old_segment)

            parent = parent_fn(current)
            if parent is None:
                anchor_point = self.root
            else:
                parent_key: str = self._key_fn(parent) if self._key_fn else parent  # type: ignore
                anchor_point = self.get(parent_key, None)

            if anchor_point:
                self.insert_segment(anchor_point, segment)
                return

            current = parent_fn(current) or self.root.data

    def _register(self, node: Node[T]):
        key: str = self._key_fn(node.data) if self._key_fn else node.data  # type: ignore
        if key in self._lookup:
            raise KeyError(f'Key already present: {key}')
        self._lookup[key] = node

    def _handle_parent_arg(self, parent: Union[str, Node[T]]) -> Node[T]:
        parent_node: Node[T]
        if isinstance(parent, str):
            parent_node = self[parent]
        elif isinstance(parent, Node):
            parent_node = parent
        else:
            raise TypeError("Parent must be a key or a node")

        return parent_node

    if support_pretty:

        def _repr_pretty_(self, p: PrettyPrinter, cycle: bool):
            if cycle:
                p.text(self.__class__.__name__ + '(<cyclic>)')
                return

            p.text('Tree ')
            p.pretty(self.root)
