'''
Based on https://bitbucket.org/hpk42/xlocal, BSD licensed.

* Updated for Python 3.6+
* Add the ability to specify defaults
* Clean up for mypy and pylint
'''

from functools import partial

try:
    from threading import get_ident as _get_ident
except ImportError:
    try:
        from _thread import get_ident as _get_ident
    except ImportError:
        from dummy_threading import get_ident as _get_ident  # type: ignore


class xlocal:
    '''Implementation of an execution local object.'''

    def __init__(self, **defaults):
        if any(key.startswith('_') for key in defaults):
            raise AttributeError("Variables cannot start with underscores")
        d = self.__dict__
        d["_get_ident"] = _get_ident
        d["_storage"] = {}
        d["_defaults"] = defaults

    def _getlocals(self, autocreate=False):
        ident = self._get_ident()
        try:
            return self._storage[ident]
        except KeyError:
            if not autocreate:
                raise
            self._storage[ident] = loc = {}
            return loc

    def _checkremove(self):
        ident = self._get_ident()
        val = self._storage.get(ident)
        if val is not None:
            if not val:
                del self._storage[ident]

    def __call__(self, **kwargs):
        '''
        Return context manager which will set execution locals for all code within the with-body.
        '''
        return WithXLocals(self, kwargs)

    def __getattr__(self, name):
        try:
            return self._getlocals()[name]
        except KeyError:
            try:
                return self._defaults[name]
            except KeyError:
                raise AttributeError(name)

    def __setattr__(self, name, val):
        raise AttributeError("xlocal stores are immutable")

    def __delattr__(self, name):
        raise AttributeError("xlocal stores are immutable")


class WithXLocals:

    def __init__(self, the_xlocal, kwargs):
        self._xlocal = the_xlocal
        self._kwargs = kwargs
        self._undostack = []

    def __enter__(self):
        loc = self._xlocal._getlocals(autocreate=True)  # pylint: disable=protected-access
        self._undostack = undostack = []
        for name, val in self._kwargs.items():
            assert name[0] != "_", "names with underscore reserved for future use"
            try:
                undostack.append(partial(loc.__setitem__, name, loc[name]))
            except KeyError:
                undostack.append(partial(loc.__delitem__, name))
            loc[name] = val
        return self

    def __exit__(self, *args):
        for action in self.__dict__.pop("_undostack"):
            action()
        self._xlocal._checkremove()  # pylint: disable=protected-access
