from typing import *

from .context import INCLUDE_METADATA, get_ctx
from .stream import MemoryStream

if INCLUDE_METADATA:
    try:
        from IPython.lib.pretty import PrettyPrinter  # type: ignore
        support_pretty = True
    except ImportError:
        support_pretty = False
else:
    support_pretty = False


class UEBase(object):
    __slots__ = ('stream', 'asset', 'start_offset', 'is_serialising', 'is_serialised', 'is_linking', 'is_linked',
                 'is_inside_array', 'parent', 'field_order', 'end_offset', 'table_index', 'users', 'field_list')

    main_field: Optional[str] = None
    string_format: Optional[str] = None
    display_fields: Optional[Sequence[str]] = None
    skip_level_field: Optional[str] = None

    def __init__(self, owner: "UEBase", stream=None):
        assert owner is not None, "Owner must be specified"
        self.stream: MemoryStream = stream or owner.stream
        self.asset = owner.asset  # type: ignore
        self.start_offset: Optional[int] = None
        self.is_serialising = False
        self.is_serialised = False
        self.is_linking = False
        self.is_linked = False
        self.is_inside_array = False
        self.field_list: List[Any] = []  # TODO: Eventually make field_list hidden behind the metadata switch
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
        if self.is_serialising:
            return

        if self.is_serialised:
            # return
            raise RuntimeError(f'Deserialise called twice for "{self.__class__.__name__}"')

        self.start_offset = self.stream.offset
        self.is_serialising = True
        self._deserialise(*args, **kwargs)
        if INCLUDE_METADATA:
            self.end_offset = self.stream.offset - 1
        self.is_serialising = False
        self.is_serialised = True

        return self

    def link(self):
        if self.is_linked or self.is_linking:
            return

        if not get_ctx().link:
            return

        self.is_linking = True
        self._link()
        self.is_linking = False
        self.is_linked = True

        return self

    def _deserialise(self, *args, **kwargs):
        raise NotImplementedError(f'Type "{self.__class__.__name__}" must implement a parse operation')

    def _link(self):
        '''Link all known fields.'''
        if not self.field_list:
            return

        self._linkValues([getattr(self, name) for name in self.field_list])

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
        if hasattr(self, name):
            raise NameError(f'Field "{name}" is already defined')

        setattr(self, name, value)
        self.field_list.append(name)

        if INCLUDE_METADATA:
            self.field_order.append(name)

        if isinstance(value, UEBase) and not value.is_serialised:
            value.deserialise(*extraArgs)

    def format_for_json(self):
        return str(self)

    def __eq__(self, other):
        return self is other  # only the same object is considered the equal

    def __hash__(self):
        return id(self)  # use the id (memory address) so each item is unique

    def __str__(self):
        '''Override string conversion to show defined fields.'''
        # TODO: Bring back string_format
        #if self.string_format:
        #    return self.string_format.format(**self.field_values)

        if self.main_field:
            return str(getattr(self, self.main_field, f'<uninitialised {self.__class__.__name__}>'))

        fields = self.display_fields or self.field_list
        fields_txt = ', '.join(str(getattr(self, name)) for name in fields)
        return f'{self.__class__.__name__}({fields_txt})'

    if support_pretty and INCLUDE_METADATA:

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

            # TODO: Bring back string_format
            #if self.string_format:
            #    p.pretty(self.string_format.format(**self.field_values))
            #    return

            fields = self.display_fields or self.field_order
            with p.group(4, self.__class__.__name__ + '(', ')'):
                if len(fields) > 1:
                    for idx, name in enumerate(fields):
                        if idx:
                            p.text(',')
                            p.breakable()
                        p.text(name + '=')
                        p.pretty(getattr(self, name))
                else:
                    p.pretty(getattr(self, fields[0]))
