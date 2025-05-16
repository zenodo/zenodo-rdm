# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Zenodo-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Script to generate known formats file.

Usage:
.. code-block:: shell

    invenio shell known_formats_gen.py
"""

import sys
import unicodedata
from pathlib import Path

import requests
import yaml
from invenio_checks.contrib.file_formats import FileFormatDatabase

FUJI_FILE_FORMATS_URL = "https://github.com/pangaea-data-publisher/fuji/raw/refs/heads/master/fuji_server/data/file_formats.yaml"

# Additional file formats to be added besides the existing F-UJI formats
ADDED_FILE_FORMATS_PATH = Path(__file__).parent / "data/added_file_formats.yaml"

# Missing extensions from the existing F-UJI formats
ENHANCED_FILE_FORMATS = {
    "microsoft_excel_file": {
        "extensions": ["xlsx"],
    },
    "hdf": {
        "extensions": ["he5"],
    },
    "newick_format": {
        "extensions": ["nwk", "newick"],
    },
    "bed_browser_extensible_data_": {
        "extensions": ["bedgraph"],
    },
    "fasta": {
        "extensions": ["fa", "fas"],
    },
    "jupyter_notebook_file": {
        "extensions": ["ipynb.json", "nb"],
    },
    "ogg_multimedia_container_format": {
        "extensions": ["spx"],
        "name": "Ogg Multimedia Container Format",
    },
    "sas_file_format": {
        "extensions": ["sas7bdat"],
    },
    "c_source_code_file": {
        "extensions": ["h"],
    },
    "matlab_format": {
        "extensions": ["mlx"],
    },
    "spss_file_format": {
        "extensions": ["zsav"],
    },
}


def fetch_fuji_file_formats_data(url: str) -> dict:
    """Fetch file formats from a URL."""
    url = url or FUJI_FILE_FORMATS_URL
    response = requests.get(url)
    if not response.ok:
        raise ValueError(f"Failed to fetch file formats from {url}")
    return yaml.safe_load(response.text)


def convert_fuji_to_known_file_formats(data: dict) -> dict:
    return {
        ff_id: {
            "name": unicodedata.normalize("NFKD", ff["name"]),
            "classifiers": ff["reason"],
            "extensions": [e.replace("*.", "") for e in ff["ext"]],
        }
        for ff_id, ff in data.items()
    }


def generate_known_file_formats(fuji_url):
    errors = []

    fuji_data = fetch_fuji_file_formats_data(fuji_url)
    known_file_formats_data = convert_fuji_to_known_file_formats(fuji_data)

    # Add additional file formats
    added_file_formats = yaml.safe_load(ADDED_FILE_FORMATS_PATH.read_text())
    known_file_formats_data.update(added_file_formats)

    # Add enhanced file formats
    for ff_id, ff in ENHANCED_FILE_FORMATS.items():
        if ff_id not in known_file_formats_data:
            errors.append(
                f"Enhanced file format {ff_id} not found in source file formats"
            )
        else:
            # raise if the extension is already present
            existing_extensions = set(known_file_formats_data[ff_id]["extensions"])
            new_extensions = set(ff["extensions"])
            already_present = existing_extensions.intersection(new_extensions)
            if already_present:
                errors.append(
                    f"Extension(s) {already_present} already present in source {ff_id}"
                )
            known_file_formats_data[ff_id]["extensions"].extend(ff["extensions"])

    if errors:
        raise ValueError(
            "Errors occurred while processing file formats:\n" + "\n".join(errors)
        )

    # Verify the data structure
    FileFormatDatabase.load(known_file_formats_data)

    yaml_output = yaml.dump(known_file_formats_data)
    return yaml_output


if __name__ == "__main__":
    if len(sys.argv) > 1:
        fuji_url = sys.argv[1]
    else:
        fuji_url = FUJI_FILE_FORMATS_URL

    try:
        yaml_output = generate_known_file_formats(fuji_url)
        print(yaml_output)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
