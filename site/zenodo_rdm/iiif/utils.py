# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""IIIF Image conversion utils."""

from pathlib import Path
import textwrap

import pyvips
from flask import current_app
from invenio_rdm_records.records.api import RDMRecord


def source_custom(input_file):
    """Custom source generator for pyvips."""

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
    """Custom target generator for pyvips."""

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
    """Base class for Image converters."""

    def convert(self, in_stream, out_stream) -> bool:
        """Convert image."""
        pass


class PyVIPSImageConverter(ImageConverter):
    """Pyvips image converter for pyramidal tifs."""

    def __init__(self, params=None):
        """Constructor."""
        self.params = params or {
            "compression": "jpeg",
            "Q": 90,
            "tile_width": 256,
            "tile_height": 256,
        }

    def convert(self, in_stream, out_stream):
        """Convert to ptifs."""
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
    """Base class for tile storage."""

    def __init__(self, *, converter: ImageConverter):
        """Constructor."""
        self.converter = converter

    def save(self, record: RDMRecord, filename: str):
        """Save tiles."""
        pass

    def open(self, record: RDMRecord, filename: str):
        """Open file in read mode."""
        pass

    def delete(self, record: RDMRecord, filename: str):
        """Delete tiles file."""
        pass


class LocalTilesStorage(TilesStorage):
    """Local tile storage implementation."""

    def __init__(self, *, base_path: str, converter: ImageConverter = None, **kwargs):
        """Constructor."""
        converter = converter or PyVIPSImageConverter()
        if Path(base_path).is_absolute():
            self.base_path = Path(base_path)
        else:
            self.base_path = Path(current_app.instance_path) / base_path
        super().__init__(converter=converter, **kwargs)

    def _get_dir(self, record: RDMRecord) -> Path:
        """Get directory."""
        # Partition record.id into 3 chunks of min. 2 characters e.g.:
        #   - "12345678" -> "/12/34/5678_"
        recid = record.pid.pid_value

        recid_parts = textwrap.wrap(recid.ljust(4, "_"), 2)
        start_parts = recid_parts[:2]
        end_parts = recid_parts[2:]
        recid_path = "/".join(start_parts)
        if end_parts:
            recid_path += f"/{''.join(end_parts)}"
        if not recid_path.endswith("_"):
            recid_path += "_"

        # e.g. images/public/12/34/5678_
        return self.base_path / record.access.protection.files / recid_path

    def _get_file_path(self, record: RDMRecord, filename: str) -> Path:
        """Get file path."""
        return self._get_dir(record) / f"{filename}.ptif"

    def save(self, record, filename):
        """Convert and save to ptif."""
        outpath = self._get_file_path(record, filename)
        if outpath.exists():
            return

        self._get_dir(record).mkdir(parents=True, exist_ok=True)
        with record.files[filename].open_stream("rb") as fin:
            fout = outpath.open("w+b")
            if not self.converter.convert(fin, fout):
                current_app.logger.info(f"Image conversion failed {record.id}")

    def open(self, record, filename):
        """Open the file in read mode."""
        return self._get_file_path(record, filename).open("rb")

    def delete(self, record, filename):
        """Delete the ptif."""
        pass
