# SPDX-FileCopyrightText: 2025 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""ZenodoRDM exporter CLI commands."""

import click
from flask.cli import with_appcontext

from zenodo_rdm.exporter.tasks import export_records


@click.group()
def exporter():
    """Exporter commands."""


@exporter.command("export-records")
@click.option(
    "-f",
    "--format",
    type=click.Choice(["json", "xml"], case_sensitive=False),
    required=True,
    help="Export format of the records.",
)
@click.option(
    "-c",
    "--community-slug",
    type=str,
    help="Slug of the community.",
)
@click.option(
    "--use-pit/--use-scan",
    default=False,
    help="Use OpenSearch Point-in-Time API instead of scroll/scan.",
)
@click.option(
    "--page-size",
    type=click.IntRange(min=1),
    default=1000,
    show_default=True,
    help="Records per search batch; larger reduces round-trips but increases memory per request.",
)
@with_appcontext
def export_records_command(format, community_slug, use_pit, page_size):
    """Export records."""
    try:
        export_records(
            format, community_slug, use_pit=use_pit, page_size=page_size
        )
        click.secho("Records exported successfully.", fg="green")
    except Exception as e:
        click.secho(f"Error exporting records: {e}", fg="red")
