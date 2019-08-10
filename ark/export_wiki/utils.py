import json
from ue.base import UEBase
def get_blueprint_path(obj):
    return f'{str(obj.namespace.value.name)}.{str(obj.name).rstrip("_C")}'

def property_serializer(obj):
    if hasattr(obj, 'format_for_json'):
        return obj.format_for_json()

    if isinstance(obj, UEBase):
        return str(obj)

    return json._default_encoder.default(obj)
