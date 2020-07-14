from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Sequence

from .context import INCLUDE_METADATA, get_ctx
from .stream import MemoryStream

if TYPE_CHECKING:
    from .asset import UAsset

if INCLUDE_METADATA:
    try:
        from IPython.lib.pretty import PrettyPrinter  # type: ignore
    except ImportError:
        PrettyPrinter = None
else:
    PrettyPrinter = None


class UEBase(object):
    main_field: Optional[str] = None
    string_format: Optional[str] = None
    display_fields: Optional[Sequence[str]] = None
    skip_level_field: Optional[str] = None

    def __init__(self, owner: UEBase, stream=None):
        assert owner is not None, "Owner must be specified"
        self.stream: MemoryStream = stream or owner.stream
        self.asset: UAsset = owner.asset  # type: ignore
        self.field_values: Dict[str, Any] = {}
        self.start_offset: Optional[int] = None
        self.is_serialised: bool = False
        self.is_linked = False
        self.is_inside_array = False
        if INCLUDE_METADATA:
            self.parent: Optional["UEBase"] = owner if owner is not owner.asset else None
            self.field_order: List[str] = []
            self.end_offset: Optional[int] = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if 'link' in vars(cls):
            raise TypeError('Cannot override "link"')
        if 'deserialise' in vars(cls):
            raise TypeError('Cannot override "deserialise"')

    def deserialise(self, *args, **kwargs):
        if self.is_serialised:
            raise RuntimeError(f'Deserialise called twice for "{self.__class__.__name__}"')

        self.start_offset = self.stream.offset
        self._deserialise(*args, **kwargs)
        if INCLUDE_METADATA:
            self.end_offset = self.stream.offset - 1
        self.is_serialised = True  # type: ignore

        return self

    def link(self):
        if self.is_linked:
            return

        if not get_ctx().link:
            return

        self._link()
        self.is_linked = True

        return self

    def _deserialise(self, *args, **kwargs):
        raise NotImplementedError(f'Type "{self.__class__.__name__}" must implement a parse operation')

    def _link(self):
        '''Link all known fields.'''
        if not self.field_values:
            return

        self._linkValues(self.field_values.values())

    def _linkValues(self, values):
        for value in values:
            if isinstance(value, UEBase):
                value.link()
            elif isinstance(value, (list, tuple)):
                self._linkValues(value)
            elif isinstance(value, dict):
                self._linkValues(value.values())

    def _newField(self, name: str, value, *extraArgs):
        '''Internal method used by subclasses to define new fields.'''
        if name in self.field_values:
            raise NameError(f'Field "{name}" is already defined')

        self.field_values[name] = value

        if INCLUDE_METADATA:
            self.field_order.append(name)

        if isinstance(value, UEBase) and not value.is_serialised:
            value.deserialise(*extraArgs)

    def __eq__(self, other):
        return self is other  # only the same object is considered the equal

    def __hash__(self):
        return id(self)  # use the id (memory address) so each item is unique

    def __getattr__(self, name: str):
        '''Override property accessor to allow reading of defined fields.'''
        try:
            return self.field_values[name]
        except KeyError:
            raise AttributeError(f'No field named "{name}"')

    def __str__(self):
        '''Override string conversion to show defined fields.'''
        if self.string_format:
            return self.string_format.format(**self.field_values)

        if self.main_field:
            return str(self.field_values.get(self.main_field, f'<uninitialised {self.__class__.__name__}>'))

        fields = self.display_fields or list(self.field_values.keys())
        fields_txt = ', '.join(str(self.field_values[name]) for name in fields)
        return f'{self.__class__.__name__}({fields_txt})'

    if PrettyPrinter:

        def _repr_pretty_(self, p: PrettyPrinter, cycle: bool):
            '''Cleanly wrappable display in Jupyter.'''
            if cycle:
                p.text(self.__class__.__name__ + '(<cyclic>)')
                return

            if self.skip_level_field:
                p.pretty(getattr(self, self.skip_level_field))
                return

            if self.main_field:
                p.pretty(getattr(self, self.main_field))
                return

            if self.string_format:
                p.pretty(self.string_format.format(**self.field_values))
                return

            fields = self.display_fields or self.field_order
            with p.group(4, self.__class__.__name__ + '(', ')'):
                if len(fields) > 1:
                    for idx, name in enumerate(fields):
                        if idx:
                            p.text(',')
                            p.breakable()
                        p.text(name + '=')
                        p.pretty(self.field_values[name])
                else:
                    p.pretty(self.field_values[fields[0]])
