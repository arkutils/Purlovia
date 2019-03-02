try:
    from IPython.lib.pretty import PrettyPrinter
    support_pretty = True
except ImportError:
    support_pretty = False

from stream import MemoryStream


class UEBase(object):
    display_fields = None

    def __init__(self, owner, stream=None):
        assert owner is not None, "Owner must be specified"
        self.stream = stream or owner.stream
        self.asset = owner.asset
        self.field_values = {}
        self.field_order = []
        self.is_serialised = False
        self.is_linked = False

    def deserialise(self, *args, **kwargs):
        if self.is_serialised:
            # return
            raise RuntimeError(f'Deserialise called twice for "{self.__class__.__name__}"')

        self.is_serialised = True
        self.start_offset = self.stream.offset
        self._deserialise(*args, **kwargs)
        self.end_offset = self.stream.offset

        return self

    def link(self):
        if self.is_linked:
            return

        self.is_linked = True
        self._link()

        return self

    def _deserialise(self, *args, **kwargs):
        raise NotImplementedError(f'Type "{self.__class__.__name__}" must implement a parse operation')

    def _link(self):
        '''Link all known fields.'''
        if len(self.field_values) == 0:
            return

        for name, value in self.field_values.items():
            if isinstance(value, UEBase):
                value.link()

    def _newField(self, name: str, value, *extraArgs):
        '''Internal method used by subclasses to define new fields.'''
        if name in self.field_order:
            raise NameError(f'Field "{name}" is already defined')

        self.field_order.append(name)
        self.field_values[name] = value

        if isinstance(value, UEBase) and not value.is_serialised:
            value.deserialise(*extraArgs)

    def __getattr__(self, name: str):
        '''Override property accessor to allow reading of defined fields.'''
        try:
            return self.field_values[name]
        except KeyError:
            raise AttributeError(f'No field named "{name}"')

    def __str__(self):
        '''Override string conversion to show defined fields.'''
        fields = self.display_fields or self.field_order
        fields_txt = ', '.join(str(self.field_values[name]) for name in fields)
        return f'{self.__class__.__name__}({fields_txt})'

    if support_pretty:

        def _repr_pretty_(self, p: PrettyPrinter, cycle: bool):
            '''Cleanly wrappable display in Jupyter.'''
            if cycle:
                p.text(self.__class__.__name__ + '(<cyclic>)')
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
