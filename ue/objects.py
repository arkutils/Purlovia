from typing import List, Optional, Tuple

from utils.log import get_logger

from .base import UEBase
from .coretypes import BulkDataHeader, NameIndex, StripDataFlags, Table
from .properties import Guid, PropertyTable, StringProperty

logger = get_logger(__name__)


class TextureMipMap(UEBase):
    display_fields = ('size_x', 'size_y', 'bulk_info')

    cooked: bool
    bulk_info: BulkDataHeader
    size_x: int
    size_y: int

    def _deserialise(self):
        self._newField('cooked', self.stream.readBool32())
        self._newField('bulk_info', BulkDataHeader(self).deserialise())

        if self.bulk_info.is_zlib_compressed:
            raise RuntimeError('Zlib compressed bulk data is not supported.')

        if self.bulk_info.is_payload_inline:
            # Bulk data is right after the header, read it although we don't know the dimensions yet.
            # self.stream.offset += self.bulk_info.size_on_disk
            self._newField('raw_data', self.stream.readBytes(self.bulk_info.size_on_disk))
        elif self.bulk_info.is_payload_at_the_end:
            # HACK: Bulk data is somewhere in the file, read it although we don't know the dimensions yet.
            saved_offset = self.asset.stream.offset
            self.asset.stream.offset = self.bulk_info.offset_in_file
            self._newField('raw_data', self.asset.stream.readBytes(self.bulk_info.size_on_disk))
            self.asset.stream.offset = saved_offset

        self._newField('size_x', self.stream.readInt32())
        self._newField('size_y', self.stream.readInt32())

    def __str__(self):
        return f'TextureMipMap ({self.size_x}x{self.size_y}, {self.bulk_info})'


class TextureData(UEBase):
    display_fields = ('size_x', 'size_y')

    size_x: int
    size_y: int
    slice_count: int
    pixel_format: StringProperty
    length: int
    mipmaps: Table

    def _deserialise(self):
        self._newField('size_x', self.stream.readInt32())
        self._newField('size_y', self.stream.readInt32())
        self._newField('slice_count', self.stream.readInt32())
        self._newField('pixel_format', StringProperty(self).deserialise())
        self._newField('unknown_field', self.stream.readInt32())
        self._newField('mipmaps', Table(self).deserialise(TextureMipMap, self.stream.readUInt32()))

    def __str__(self):
        return f'TextureData ({self.pixel_format}, {len(self.mipmaps)}x {self.size_x}x{self.size_y})'


class Texture2D(UEBase):
    display_fields = ()

    values: List["TextureData"]
    strip_flags: StripDataFlags

    def _deserialise(self, properties: PropertyTable):  # type: ignore
        self._newField('strip_flags', StripDataFlags(self))
        strip_flags2 = StripDataFlags(self).deserialise()
        assert self.strip_flags.global_flags == strip_flags2.global_flags
        assert self.strip_flags.class_flags == strip_flags2.class_flags

        values = []
        self._newField('is_cooked', self.stream.readBool32())
        while self.is_cooked and self.stream.offset < (self.stream.end - 8):
            value = self._parse_platform_data()
            if value is None:
                break
            values.append(value)
        self._newField('values', values)

    def _parse_platform_data(self) -> Optional[TextureData]:
        pixel_format = NameIndex(self).deserialise()
        pixel_format.link()
        if pixel_format.index is self.asset.none_index:
            return None

        next_offset = self.stream.readUInt32()
        platform_data = TextureData(self).deserialise()
        platform_data.link()

        if self.stream.offset != next_offset:
            logger.warning(
                f'Read of texture data could have failed: skipping to {next_offset} (+{next_offset - self.stream.offset})')
            self.stream.offset = next_offset
        assert str(platform_data.pixel_format) == str(pixel_format)
        return platform_data


class CompressedAudioChunk(UEBase):
    display_fields = ()

    def _deserialise(self):
        self._newField('format_name', NameIndex(self))
        self._newField('bulk_data', BulkDataHeader(self).deserialise())
        # Name table should be linked at this point.
        self.format_name.link()


class StreamedAudioChunk(UEBase):
    display_fields = ()

    def _deserialise(self):
        self._newField('cooked', self.stream.readBool32())
        self._newField('bulk_data', BulkDataHeader(self).deserialise())
        self._newField('data_size', self.stream.readInt32())


class SoundWave(UEBase):
    def _deserialise(self, properties: PropertyTable):  # type: ignore
        self._newField('is_cooked', self.stream.readBool32())
        self._newField('compression_name', NameIndex(self))
        self.compression_name.link()

        streaming_enabled = properties.get_property('bReallyUseStreamingReserved', fallback=False)
        if streaming_enabled:
            # This is either some early streaming implementation,
            # or it's been heavily modified in Ark, the GUID location
            # and second "cooked" bool being most notable.
            self._newField('guid', Guid(self))
            self._newField('is_streaming_cooked', self.stream.readBool32())
            if self.is_streaming_cooked:
                chunk_count = self.stream.readUInt32()
                self._newField('streamed_format', NameIndex(self))
                self.streamed_format.link()
                assert str(self.streamed_format) == str(self.compression_name)
                self._newField('streaming_chunks', Table(self).deserialise(StreamedAudioChunk, chunk_count))
        else:
            # Asset streaming is disabled.
            if self.is_cooked:
                chunk_count = self.stream.readUInt32()
                self._newField('compressed_chunks', Table(self).deserialise(CompressedAudioChunk, chunk_count))
            else:
                self._newField('bulk_data', BulkDataHeader(self).deserialise())
            self._newField('guid', Guid(self))


class InstancedStaticMeshComponentObject(UEBase):

    visible_instances: List[Tuple[float, float, float]]

    def _deserialise(self, properties: PropertyTable):  # type:ignore
        lod_count = self.stream.readUInt32()

        for index in range(lod_count):
            strip_flags = StripDataFlags(self).deserialise()

            if not strip_flags.is_stripped_for_custom(1):
                has_color_data = self.stream.readBool8()
                if has_color_data:
                    color_strip = StripDataFlags(self).deserialise()
                    self.stream.offset += 4
                    color_num = self.stream.readUInt32()

                    # Required for client data to be parsed.
                    if color_num > 0 and not color_strip.is_stripped_for_server():
                        self.stream.offset += 4 * color_num

        size = self.stream.readUInt32()
        num_instances = self.stream.readUInt32()
        instances = []

        for index in range(num_instances):
            # TODO: check if instance is visible

            # Each instance is described as a 4x4 matrix. Last row describes the origin.
            # Discarding scale and rotation to keep only the origin.
            self.stream.offset += 4 * 3 * 4  # 3 rows with 4 values each 4 bytes long
            x, y, z = (self.stream.readFloat(), self.stream.readFloat(), self.stream.readFloat())
            # One more value that might be used as part of scaling.
            self.stream.offset += 4
            # These are UV biases we don't need. Removed in later engine releases.
            self.stream.offset += 16

            instances.append((x, y, z))

        self._newField('visible_instances', instances)


AFTER_PROPERTY_TABLE_TYPES = {
    # 'Texture2D': Texture2D,
    # 'SoundWave': SoundWave,
    'HierarchicalInstancedStaticMeshComponent': InstancedStaticMeshComponentObject,
}
