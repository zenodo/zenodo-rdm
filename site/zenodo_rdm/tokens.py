# SPDX-FileCopyrightText: 2023 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
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
