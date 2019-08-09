from operator import attrgetter

from .tree import IndexedTree, Node


def test_simple_string_node_tree():
    t = Node[str]('root')
    t.add('a')
    t.add('b')
    assert repr(t.nodes) == "[Node('a'), Node('b')]"

    t.nodes[0].add('a1')
    assert repr(t.nodes[0].nodes) == "[Node('a1')]"

    found = []
    t.walk(lambda n: found.append(n.data))
    assert repr(found) == "['root', 'a', 'a1', 'b']"


def test_indexed_simple_string_tree():
    t = IndexedTree[str]('root', lambda data: data)
    a = t.add('root', 'a')
    b = t.add('root', 'b')
    assert id(a) == id(t['a'])
    assert id(b) == id(t['b'])
    assert repr(t['root'].nodes) == "[Node('a'), Node('b')]"

    t.add('a', 'a1')
    assert repr(t['a'].nodes) == "[Node('a1')]"

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

    t.nodes[0].add(MyDataType('a1'))
    assert repr(t.nodes[0].nodes) == "[Node(MyDataType('a1'))]"


def test_indexed_typed_tree():
    t = IndexedTree[MyDataType](MyDataType('root'), attrgetter('name'))
    a = t.add('root', MyDataType('a'))
    b = t.add('root', MyDataType('b'))
    assert id(a) == id(t['a'])
    assert id(b) == id(t['b'])
    assert repr(t['root'].nodes) == "[Node(MyDataType('a')), Node(MyDataType('b'))]"

    t.add('a', MyDataType('a1'))
    assert repr(t['a'].nodes) == "[Node(MyDataType('a1'))]"

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
