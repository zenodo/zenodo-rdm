# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Zenodo is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo tokens."""

from marshmallow import Schema, fields


class RATSubjectSchema(Schema):
    """Resource access token JWT subject schema."""

    pid_value = fields.Function(
        deserialize=lambda x: str(x),
        data_key="deposit_id",
        required=True,
    )
    file_key = fields.Str(data_key="file", missing=None)
    permission = fields.Str(data_key="access", missing=None)
