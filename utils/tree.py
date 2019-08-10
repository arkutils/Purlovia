'''
Reusable tree structure, including a variant with a fast indexed lookup.
'''
from __future__ import annotations

from typing import Callable, Dict, Generic, List, TypeVar, Union

__all__ = [
    'Node',
    'IndexedTree',
]

T = TypeVar('T')

MISSING = object()


class Node(Generic[T]):
    def __init__(self, data: T):
        self._data: T = data
        self._nodes: List[Node[T]] = list()

    @property
    def data(self) -> T:
        return self._data

    @property
    def nodes(self) -> List[Node[T]]:
        return self._nodes

    def walk(self, fn: Callable[[Node], None]):
        fn(self)
        for node in self.nodes:
            node.walk(fn)

    def add(self, data: Union[T, Node[T]]) -> Node[T]:
        if not isinstance(data, Node):
            data = Node[T](data)
        self._nodes.append(data)
        return data

    def __repr__(self):
        return f'{self.__class__.__name__}({self._data!r})'


class IndexedTree(Generic[T]):
    def __init__(self, root: T, key_fn: Callable[[T], str]):
        self._key_fn = key_fn
        self._lookup: Dict[str, Node[T]] = dict()
        self.root: Node[T] = Node[T](root)
        self._register(self.root)

    def add(self, parent: Union[str, Node[T]], data: Union[T, Node[T]]) -> Node[T]:
        parent_node = self._handle_parent_arg(parent)

        if not isinstance(data, Node):
            data = Node[T](data)

        self._register(data)
        parent_node.nodes.append(data)

        return data

    def insert_segment(self, parent: Union[str, Node[T]], partial_tree: Node[T]):
        parent_node = self._handle_parent_arg(parent)
        partial_tree.walk(self._register)
        parent_node.nodes.append(partial_tree)

    def __getitem__(self, key: str):
        return self._lookup[key]

    def __contains__(self, key: str):
        return key in self._lookup

    def get(self, key: str, fallback=MISSING):
        if fallback is MISSING:
            return self._lookup[key]
        else:
            return self._lookup.get(key, fallback)

    def _register(self, node: Node[T]):
        key = self._key_fn(node.data)
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
