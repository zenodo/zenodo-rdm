# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo migrator metadata entry transformer mixin."""


class ZenodoFilesEntryMixin:
    """Zenodo files entry mixin."""

    ns_key = None

    def get_field(self, entry, key):
        """Retrieve entry key."""
        if self.ns_key is None:
            raise NotImplementedError(
                "You must define a namespace key to use this mixin."
            )
        return entry[f"{self.ns_key}{key}"]
