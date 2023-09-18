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
        if not (openaire_type(record)):
            return

        serializer = OpenAIREV1Serializer()
        serialized_record = serializer.dump_obj(record)
        url = "{}/feedObject".format(current_app.config["OPENAIRE_API_URL"])
        request = openaire_request_factory()
        res = request.post(url, data=serialized_record, timeout=10)

        if not res.ok:
            raise OpenAIRERequestError(res.text)

        res_beta = None
        if current_app.config["OPENAIRE_API_URL_BETA"]:
            url_beta = "{}/feedObject".format(
                current_app.config["OPENAIRE_API_URL_BETA"]
            )
            res_beta = request.post(url_beta, data=serialized_record, timeout=10)

        if res_beta and not res_beta.ok:
            raise OpenAIRERequestError(res_beta.text)
        else:
            recid = record.get("recid")
            current_cache.delete("openaire_direct_index:{}".format(recid))
    except Exception as exc:
        recid = record.get("recid")
        current_cache.set(
            "openaire_direct_index:{}".format(recid), datetime.now(), timeout=-1
        )
        if retry:
            openaire_direct_index.retry(exc=exc)
        else:
            raise exc
