# SPDX-FileCopyrightText: 2025 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Script to export all records in XML format.

Usage:

.. code-block:: shell

    ./scripts/run_script.py scripts/export-all-xml.py
"""

from invenio_app.factory import create_api
from zenodo_rdm.exporter.tasks import export_records


def export_all_xml():
    """Export records."""
    format = "xml"
    community_slug = None
    try:
        export_records(format, community_slug)
        print(f"Records exported successfully.")
    except Exception as e:
        print(f"Error exporting records: {e}")


if __name__ == "__main__":
    with create_api().app_context():
        export_all_xml()
