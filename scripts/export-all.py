# SPDX-FileCopyrightText: 2025 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Script to export all records in JSON and DataCite XML formats.

Usage:

.. code-block:: shell

    ./scripts/run_script.py scripts/export-all.py
"""

from invenio_app.factory import create_api
from zenodo_rdm.exporter.tasks import export_records


def export_all():
    """Export records."""
    formats = ("json", "xml")
    community_slug = None
    try:
        export_records(formats, community_slug)
        print("Records exported successfully.")
    except Exception as e:
        print(f"Error exporting records: {e}")
        raise


if __name__ == "__main__":
    with create_api().app_context():
        export_all()
