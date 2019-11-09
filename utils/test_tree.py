from operator import attrgetter

import pytest  # type: ignore

from .tree import IndexedTree, Node


@pytest.fixture(name='basic_tree')
def fixture_basic_tree() -> Node[str]:
    t = Node[str]('root')
    t.add('a')
    t.add('b')
    t.nodes[0].add('a1')
    t.nodes[1].add('b1')
    t.nodes[1].add('b2')
    return t


def test_construct_simple_string_node_tree():
    t = Node[str]('root')
    t.add('a')
    t.add('b')
    assert repr(t.nodes) == "[Node('a'), Node('b')]"
    assert t.nodes[0].parent is t
    assert t.nodes[1].parent is t

    t.nodes[0].add('a1')
    assert repr(t.nodes[0].nodes) == "[Node('a1')]"
    assert t.nodes[0].nodes[0].parent is t.nodes[0]


def test_walk_nodes(basic_tree: Node[str]):
    found = []
    basic_tree.walk(lambda n: found.append(n.data))
    assert repr(found) == "['root', 'a', 'a1', 'b', 'b1', 'b2']"


def test_walk_iterator_dfs(basic_tree: Node[str]):
    found = [node.data for node in basic_tree.walk_iterator(skip_self=False)]
    assert repr(found) == "['root', 'a', 'a1', 'b', 'b1', 'b2']"


def test_walk_iterator_bfs(basic_tree: Node[str]):
    found = [node.data for node in basic_tree.walk_iterator(skip_self=False, breadth_first=True)]
    assert repr(found) == "['root', 'a', 'b', 'a1', 'b1', 'b2']"


def test_walk_iterator_without_self_dfs(basic_tree: Node[str]):
    found = [node.data for node in basic_tree.walk_iterator(skip_self=True)]
    assert repr(found) == "['a', 'a1', 'b', 'b1', 'b2']"


def test_walk_iterator_without_self_bfs(basic_tree: Node[str]):
    found = [node.data for node in basic_tree.walk_iterator(skip_self=True, breadth_first=True)]
    assert repr(found) == "['a', 'b', 'a1', 'b1', 'b2']"


def test_walk_abort(basic_tree: Node[str]):
    found = []

    def walker(n):
        found.append(n.data)
        return False if n.data == 'a1' else None

    basic_tree.walk(walker)
    assert repr(found) == "['root', 'a', 'a1']"


def test_indexed_simple_string_tree():
    t = IndexedTree[str]('root', lambda data: data)
    a = t.add('root', 'a')
    b = t.add('root', 'b')
    assert id(a) == id(t['a'])
    assert id(b) == id(t['b'])
    assert repr(t['root'].nodes) == "[Node('a'), Node('b')]"
    assert t['a'].parent is t.root
    assert t['b'].parent is t.root

    t.add('a', 'a1')
    assert repr(t['a'].nodes) == "[Node('a1')]"
    assert t['a1'].parent is t['a']

    found = []
    t.root.walk(lambda n: found.append(n.data))
    assert repr(found) == "['root', 'a', 'a1', 'b']"


class MyDataType:
    def __init__(self, name: str):
        self.name = name

    def __repr__(self):
        return f'{self.__class__.__name__}({self.name!r})'


def test_typed_node_tree():
    t = Node[MyDataType](MyDataType('root'))
    t.add(MyDataType('a'))
    t.add(MyDataType('b'))
    assert repr(t.nodes) == "[Node(MyDataType('a')), Node(MyDataType('b'))]"
    assert t.nodes[0].parent is t
    assert t.nodes[1].parent is t

    t.nodes[0].add(MyDataType('a1'))
    assert repr(t.nodes[0].nodes) == "[Node(MyDataType('a1'))]"
    assert t.nodes[0].nodes[0].parent is t.nodes[0]


def test_indexed_typed_tree():
    t = IndexedTree[MyDataType](MyDataType('root'), attrgetter('name'))
    a = t.add('root', MyDataType('a'))
    b = t.add('root', MyDataType('b'))
    assert id(a) == id(t['a'])
    assert id(b) == id(t['b'])
    assert repr(t['root'].nodes) == "[Node(MyDataType('a')), Node(MyDataType('b'))]"
    assert t.root.nodes[0].parent is t.root
    assert t.root.nodes[1].parent is t.root

    t.add('a', MyDataType('a1'))
    assert repr(t['a'].nodes) == "[Node(MyDataType('a1'))]"
    assert t.root.nodes[0].nodes[0].parent is t.root.nodes[0]

    found = []
    t.root.walk(lambda n: found.append(n.data))
    assert repr(found) == "[MyDataType('root'), MyDataType('a'), MyDataType('a1'), MyDataType('b')]"


def test_insert_segment():
    # Make an indexed tree
    t = IndexedTree[MyDataType](MyDataType('root'), attrgetter('name'))
    t.add('root', MyDataType('a'))
    t.add('root', MyDataType('b'))

    # Make a simple separate tree segment
    n = Node[str](MyDataType('segment'))
    na = n.add(MyDataType('na'))
    n.add(MyDataType('nb'))
    na.add(MyDataType('naa'))

    # Shove it right in there
    t.insert_segment('b', n)
    assert 'segment' in t
    assert 'naa' in t

    assert repr(t['naa']) == "Node(MyDataType('naa'))"
    assert repr(t['b'].nodes) == "[Node(MyDataType('segment'))]"
    assert repr(t['segment'].nodes) == "[Node(MyDataType('na')), Node(MyDataType('nb'))]"
    assert repr(t['na'].nodes) == "[Node(MyDataType('naa'))]"

    # Ensure parent chain extends into segment completely
    assert t['naa'].parent is t['na']
    assert t['segment'].parent is t['b']
