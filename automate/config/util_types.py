from typing import Dict, Iterable

__all__ = [
    'IniStringList',
    'ModIdAccess',
]


class IniStringList(list):
    '''A validated type that converts a newline-separated string list into a proper Python list.'''
    @classmethod
    def __get_validators__(cls):
        yield cls.convert

    @classmethod
    def convert(cls, v):
        if isinstance(v, (list, tuple)):
            return v
        if isinstance(v, str):
            v = v.strip().replace('\r\n', '\n').split('\n')
            return v
        raise ValueError('Expected string list')


class ModIdAccess:
    '''Provide bi-directional access to a modid <-> tag dictionary.'''
    ids_to_tags: Dict[str, str]
    tags_to_ids: Dict[str, str]

    def __init__(self, source: Dict[str, str], keyed_by_id=False):
        if keyed_by_id:
            self.ids_to_tags = {k.lower(): v for k, v in source.items()}
            self.tags_to_ids = {v.lower(): k for k, v in source.items()}
        else:
            self.ids_to_tags = {v.lower(): k for k, v in source.items()}
            self.tags_to_ids = {k.lower(): v for k, v in source.items()}

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value):
        return value

    def ids(self) -> Iterable[str]:
        return self.tags_to_ids.values()

    def tags(self) -> Iterable[str]:
        return self.ids_to_tags.values()

    def id_from_tag(self, tag: str):
        return self.tags_to_ids.get(tag.lower(), None)

    def tag_from_id(self, modid: str):
        return self.ids_to_tags.get(modid.lower(), None)
