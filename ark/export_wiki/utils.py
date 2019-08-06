def get_blueprint_path(obj):
    return f'{str(obj.namespace.value.name)}.{str(obj.name).rstrip("_C")}'
