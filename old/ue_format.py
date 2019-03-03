from structex import Format, Type, Struct

Struct._format = '<'


class Guid(Struct):
    a = Type.uint32
    b = Type.uint32
    c = Type.uint32
    d = Type.uint32


class ChunkPtr(Struct):
    count = Type.uint32
    offset = Type.uint32


class ImportTableItem(Struct):
    package = Type.int64
    klass = Type.int64
    outer_index = Type.int32
    name = Type.int64


class ExportTableItem(Struct):
    klass = Type.int32
    super = Type.int32
    outer_index = Type.int32
    name = Type.int64
    object_flags = Type.uint32
    serial_size = Type.uint32
    serial_offset = Type.uint32
    force_export = Type.bool32  # ExportFlags
    not_for_client = Type.bool32
    not_for_server = Type.bool32
    guid = Type.Struct(Guid)
    package_flags = Type.uint32
    not_for_editor_game = Type.bool32


class HeaderTop(Struct):
    tag = Type.uint32
    legacy_ver = Type.int32
    ue_ver = Type.int32
    file_ver = Type.uint32
    licensee_ver = Type.uint32
    engine = Type.uint32
    header_size = Type.uint32


class HeaderTables(Struct):
    package_flags = Type.uint32
    names_chunk = Type.Struct(ChunkPtr)
    exports_chunk = Type.Struct(ChunkPtr)
    imports_chunk = Type.Struct(ChunkPtr)
    depends_offset = Type.uint32


class HeaderBottom(Struct):
    string_assets = Type.Struct(ChunkPtr)
    thumbnail_offset = Type.uint32
    guid = Type.Struct(Guid)


class BlueprintField(Struct):
    name = Type.uint64
    field_type = Type.uint64
    size = Type.uint32
    index = Type.uint32
    # ...value


class StructProperty(Struct):
    owner_name_i = Type.int64

    item_name_i = Type.int64
    type1_name_i = Type.int64  # always ArrayProperty?
    count1 = Type.int64  # ???
    type2_name_i = Type.int64  # actual type of first field
    count2 = Type.int32  # count of first field - only seen 1 so far
    value1 = Type.float  # TEST ONLY - shouldn't be hardcoded
