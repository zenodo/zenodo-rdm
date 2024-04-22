from pathlib import Path
from textwrap import wrap

from flask import current_app


from invenio_rdm_records.records.api import RDMRecord
import pyvips


def source_custom(input_file):

    def read_handler(size):
        return input_file.read(size)

    # seek is optional, but may improve performance by reducing buffering
    def seek_handler(offset, whence):
        input_file.seek(offset, whence)
        return input_file.tell()

    source = pyvips.SourceCustom()
    source.on_read(read_handler)
    source.on_seek(seek_handler)

    return source


def target_custom(output_file):
    def write_handler(chunk):
        return output_file.write(chunk)

    def read_handler(size):
        return output_file.read(size)

    def seek_handler(offset, whence):
        output_file.seek(offset, whence)
        return output_file.tell()

    def end_handler():
        try:
            output_file.close()
        except IOError:
            return -1
        else:
            return 0

    target = pyvips.TargetCustom()
    target.on_write(write_handler)
    target.on_read(read_handler)
    target.on_seek(seek_handler)
    target.on_end(end_handler)

    return target


class ImageConverter:

    def convert(self, in_stream, out_stream) -> bool:
        pass


class PyVIPSImageConverter(ImageConverter):

    def __init__(self, params=None):
        self.params = params or {
            "compression": "jpeg",
            "Q": 90,
            "tile_width": 256,
            "tile_height": 256,
        }

    def convert(self, in_stream, out_stream):
        try:
            source = source_custom(in_stream)

            target = target_custom(out_stream)
            image = pyvips.Image.new_from_source(source, "", access="sequential")
            image.tiffsave_target(target, tile=True, pyramid=True, **self.params)
            return True
        except pyvips.Error:
            current_app.logger.exception("Image processing with pyvips failed")
            return False


class TilesStorage:

    def __init__(self, *, converter: ImageConverter):
        self.converter = converter

    def save(self, record: RDMRecord, filename: str):
        pass

    def open(self, record: RDMRecord, filename: str):
        pass

    def delete(self, record: RDMRecord, filename: str):
        pass


class LocalTilesStorage(TilesStorage):

    def __init__(self, *, base_path: str, converter: ImageConverter = None, **kwargs):
        converter = converter or PyVIPSImageConverter()
        self.base_path = Path(base_path)
        super().__init__(converter=converter, **kwargs)

    def _get_dir(self, record: RDMRecord) -> Path:
        rec_id = record.pid.pid_value
        path_partitions = wrap(rec_id, width=3)
        return self.base_path / record.access.protection.files / Path(*path_partitions) / rec_id

    def _get_file_path(self, record: RDMRecord, filename: str) -> Path:
        # Partition record.id into 3 chunks of min. 2 characters (e.g. "12345678" -> ["12", "34", "5678"])
        return self._get_dir(record) / (filename + ".ptif")

    def save(self, record, filename):
        outpath = self._get_file_path(record, filename)
        if outpath.exists():
            return

        self._get_dir(record).mkdir(parents=True, exist_ok=True)
        with record.files[filename].open_stream("rb") as fin:
            fout = outpath.open("w+b")
            if not self.converter.convert(fin, fout):
                current_app.logger.info(f"Image conversion failed {record.id}")

    def open(self, record, filename):
        return self._get_file_path(record, filename).open("rb")

    def delete(self, record, filename):
        self._get_file_path(record, filename).unlink()
        return True
