# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Migrator extraction classes for multiple sources (PGSQL, JSONL files)."""

import json

import psycopg
from invenio_rdm_migrator.extract import Extract


class JSONLExtract(Extract):
    """Data extraction from JSONL files."""

    def __init__(self, filepath):
        """Constructor."""
        self.filepath = filepath

    def run(self):
        """Yield one element at a time."""
        with open(self.filepath, "r") as reader:
            for line in reader:
                # TODO JSONl file should be cleaned up before loading
                line = line.strip().replace("\\\\", "\\")
                yield json.loads(line)


class PostgreSQLExtract(Extract):
    """Data extraction from a PostgreSQL database."""

    def __init__(self, db_uri, query):
        """Constructor."""
        self.db_uri = db_uri
        self.query = query

    def run(self):
        """Yield one element at a time."""
        with psycopg.connect(self.db_uri) as conn, conn.cursor() as cur:
            with cur.copy(self.query) as copy:
                copy.set_types(["json"])
                yield from copy.rows()


EXTRACT_USERS_SQL = """
COPY (
    SELECT row_to_json(users)
    FROM (
        SELECT
            u.*,
            up.*,
            coalesce(user_t.tokens, null) AS tokens,
            coalesce(user_i.identities, null) AS identities,
            coalesce(user_sa.session_activity, null) AS session_activity
        FROM accounts_user AS u
        JOIN userprofiles_userprofile up ON u.id = up.user_id
        LEFT JOIN LATERAL (
            SELECT json_agg(row_to_json(_t)) AS tokens
            FROM (
                SELECT t.*, c.name
                FROM oauth2server_token AS t
                JOIN oauth2server_client c ON t.client_id = c.client_id
                WHERE t.user_id = u.id
                    AND t.is_personal = true
                    AND t.is_internal = false
            ) as _t
        ) AS user_t ON true
        LEFT JOIN LATERAL (
            SELECT json_agg(row_to_json(i)) AS identities
            FROM oauthclient_useridentity AS i
            WHERE i.id_user = u.id
        ) AS user_i ON true
        LEFT JOIN LATERAL (
            SELECT json_agg(row_to_json(sa)) AS session_activity
            FROM accounts_user_session_activity AS sa
            WHERE sa.user_id = u.id
        ) AS user_sa ON true
    ) as users
) TO STDOUT;
"""

EXTRACT_RECORDS_SQL = """
    COPY (
        SELECT row_to_json(records)
        FROM (
            SELECT
                r.*, pr.index
            FROM records_metadata as r
                JOIN pidstore_pid
                    ON pidstore_pid.object_uuid = r.id
                JOIN pidrelations_pidrelation as pr
                    ON pidstore_pid.id = pr.child_id
            WHERE
                pidstore_pid.pid_type = 'recid' AND
                pidstore_pid.status = 'R' AND
                pidstore_pid.object_type = 'rec'
        ) as records
    ) TO STDOUT;
"""

EXTRACT_REQUESTS_SQL = """
COPY (
    SELECT row_to_json(requests)
    FROM (
        WITH active_communities AS (
            SELECT DISTINCT(id_community) FROM communities_community_record
                INNER JOIN communities_community ON id_community=id
                WHERE id_community NOT IN ('zenodo', 'ecfunded')
                    AND deleted_at IS NULL
        ), records_ir AS (
            SELECT
                cr.created,
                cr.updated,
                (r.json->>'conceptrecid')::character varying AS conceptrecid,
                (r.json->>'recid')::character varying AS recid,
                cr.id_community,
                (r.json#>>'{owners, 0}')::character varying AS owners,
                (r.json->>'title')::character varying AS title
            FROM records_metadata AS r INNER JOIN communities_community_record AS cr
                ON id_record = id
                WHERE id_community NOT IN ('zenodo', 'ecfunded')
                    AND r.json->>'conceptrecid' IS NOT NULL
        ), records_pid AS (
            SELECT
                records_ir.created,
                records_ir.updated,
                records_ir.id_community,
                records_ir.conceptrecid,
                records_ir.recid,
                pidstore_pid.id as pid_id,
                records_ir.owners,
                records_ir.title
            FROM pidstore_pid INNER JOIN records_ir
                ON pid_value=records_ir.recid
                WHERE pid_type='recid' AND status!= 'D'
        ), records_index AS (
            SELECT
                records_pid.created,
                records_pid.updated,
                records_pid.id_community,
                records_pid.conceptrecid,
                records_pid.recid,
                pr.index,
                records_pid.owners,
                records_pid.title
            FROM records_pid INNER JOIN pidrelations_pidrelation AS pr
                ON pid_id = pr.child_id
        ), concept_last_version AS (
            SELECT conceptrecid, MAX(index) as max_index
            FROM records_index GROUP BY conceptrecid
        ), active_records AS (
            SELECT
                created,
                updated,
                id_community,
                ri.conceptrecid,
                recid,
                owners,
                title
            FROM records_index AS ri INNER JOIN concept_last_version AS clv
            ON ri.conceptrecid = clv.conceptrecid AND index = max_index
        )
        SELECT
            ar.created,
            ar.updated,
            ac.id_community,
            ar.conceptrecid,
            ar.recid,
            ar.owners,
            ar.title
        FROM active_records AS ar INNER JOIN active_communities AS ac
            ON ar.id_community=ac.id_community
    ) as requests
) TO STDOUT;
"""

EXTRACT_COMMUNITIES_SQL = """
COPY (
    SELECT
        row_to_json(communities)
    FROM
        (
            SELECT
                r.*,
                CASE
                    WHEN featured_comm.start_date IS NULL THEN FALSE
                    ELSE TRUE
                END as is_featured,
                featured_comm.start_date as featured_start_date,
                featured_comm.created as featured_created,
                featured_comm.updated as featured_updated
            FROM
                communities_community as r
                LEFT OUTER JOIN communities_featured_community featured_comm ON r.id = featured_comm.id_community
        ) as communities
) TO STDOUT;
"""
