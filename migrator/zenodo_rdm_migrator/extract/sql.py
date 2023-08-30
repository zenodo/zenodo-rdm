# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Migrator SQL extraction."""

EXTRACT_OAUTH_2_SERVER_TOKENS = """
COPY (
    SELECT row_to_json(tokens)
    FROM (
        SELECT
            id,
            client_id,
            user_id,
            token_type,
            convert_from(access_token, "utf-8") as access_token,
            convert_from(refresh_token, "utf-8") as refresh_token,
            expires,
            _scopes,
            is_personal,
            is_internal
        FROM oauth2server_token
    ) as tokens
) TO STDOUT;
"""
