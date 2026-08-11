# SPDX-FileCopyrightText: 2025 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""ZenodoRDM exporter CLI commands."""

import click
from flask.cli import with_appcontext

from zenodo_rdm.exporter.tasks import export_records
from zenodo_rdm.exporter.writers import EXPORT_FORMATS


@click.group()
def exporter():
    """Exporter commands."""


@exporter.command("export-records")
@click.option(
    "-f",
    "--format",
    "formats",
    type=click.Choice(EXPORT_FORMATS, case_sensitive=False),
    multiple=True,
    required=True,
    help="Record format. Repeat to export more than one format.",
)
@click.option(
    "-c",
    "--community-slug",
    type=str,
    help="Slug of the community.",
)
@with_appcontext
def export_records_command(formats, community_slug):
    """Export records."""
    try:
        export_records(formats, community_slug)
        click.secho("Records exported successfully.", fg="green")
    except Exception as e:
        raise click.ClickException(f"Error exporting records: {e}") from e
