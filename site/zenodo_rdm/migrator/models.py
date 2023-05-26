# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Dataclasses user models to generate table rows."""

from dataclasses import InitVar, dataclass


@dataclass
class Funders:
    """Funders dataclass model."""

    id: str
    created: str
    updated: str
    json: dict
    version_id: int
    pid: str

    _table_name: InitVar[str] = "funder_metadata"


@dataclass
class Awards:
    """Awards dataclass model."""

    id: str
    created: str
    updated: str
    json: dict
    version_id: int
    pid: str

    _table_name: InitVar[str] = "award_metadata"
