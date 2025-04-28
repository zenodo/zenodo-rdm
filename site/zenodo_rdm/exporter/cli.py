# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

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
@with_appcontext
def export_records_command(format, community_slug):
    """Export records."""
    try:
        export_records(format, community_slug)
        click.secho(f"Records exported successfully.", fg="green")
    except Exception as e:
        click.secho(f"Error exporting records: {e}", fg="red")
