# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Zenodo-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""OpenAIRE celery tasks."""

from datetime import datetime

from celery import shared_task
from flask import current_app
from invenio_access.permissions import system_identity
from invenio_cache import current_cache
from invenio_rdm_records.proxies import current_rdm_records_service as records_service

from .errors import OpenAIRERequestError
from .serializers import OpenAIREV1Serializer
from .utils import openaire_request_factory, openaire_type


@shared_task(
    ignore_result=True,
    max_retries=6,
    default_retry_delay=4 * 60 * 60,
    rate_limit="100/m",
)
def openaire_direct_index(record_id, retry=True):
    """Send record for direct indexing at OpenAIRE.

    :param record_id: Record Metadata UUID.
    :type record_id: str
    """
    try:
        record = records_service.read(system_identity, record_id)

        # Bail out if not an OpenAIRE record.
        if not (openaire_type(record.data)):
            return

        # Serialize record for OpenAIRE indexing
        serializer = OpenAIREV1Serializer()
        serialized_record = serializer.dump_obj(record.data)

        # Build the request
        openaire_api_url = current_app.config["OPENAIRE_API_URL"]
        url = f"{openaire_api_url}/feedObject"
        request = openaire_request_factory()
        res = request.post(url, data=serialized_record, timeout=10)

        if not res.ok:
            raise OpenAIRERequestError(res.text)

        beta_url = current_app.config.get("OPENAIRE_API_URL_BETA")
        if beta_url:
            beta_endpoint = f"{beta_url}/feedObject"
            res_beta = request.post(beta_endpoint, data=serialized_record, timeout=10)

            if not res_beta.ok:
                raise OpenAIRERequestError(res_beta.text)
        recid = record["id"]
        current_cache.delete(f"openaire_direct_index:{recid}")
    except Exception as exc:
        current_cache.set(
            "openaire_direct_index:{}".format(record_id), datetime.now(), timeout=-1
        )
        if retry:
            openaire_direct_index.retry(exc=exc)
        else:
            raise exc
