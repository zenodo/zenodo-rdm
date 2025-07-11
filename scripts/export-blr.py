# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Zenodo-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Script to export Biodiversity Literature Repository (BLR) records in JSON format.

Usage:

.. code-block:: shell

    ./scripts/run_script.py scripts/export-blr.py
"""

from invenio_app.factory import create_api
from zenodo_rdm.exporter.tasks import export_records


def export_blr():
    """Export records."""
    format = "json"
    community_slug = "biosyslit"
    try:
        export_records(format, community_slug)
        print(f"Records exported successfully.")
    except Exception as e:
        print(f"Error exporting records: {e}")


if __name__ == "__main__":
    with create_api().app_context():
        export_blr()
