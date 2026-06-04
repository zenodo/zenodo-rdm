# SPDX-FileCopyrightText: 2023 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""OpenAIRE celery tasks."""

from datetime import datetime
from functools import wraps

from celery import shared_task
from flask import current_app
from invenio_access.permissions import system_identity
from invenio_cache import current_cache
from invenio_rdm_records.proxies import current_rdm_records_service as records_service
from werkzeug.local import LocalProxy

from .errors import OpenAIREInvalidRecordError, OpenAIRERequestError
from .serializers import OpenAIREV1Serializer
from .utils import get_openaire_id, openaire_request_factory, openaire_type

is_openaire_enabled = LocalProxy(
    lambda: current_app.config["OPENAIRE_DIRECT_INDEXING_ENABLED"]
)


def execute_if_openaire_enabled():
    """Execute task if OpenAIRE is enabled."""

    def decorator(f):
        @wraps(f)
        def inner(*args, **kwargs):
            if is_openaire_enabled:
                return f(*args, **kwargs)
            return None

        return inner

    return decorator


@shared_task(
    ignore_result=True,
    max_retries=6,
    default_retry_delay=10 * 60,  # 10 minutes
    rate_limit="100/m",
)
@execute_if_openaire_enabled()
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
        base_url = current_app.config["OPENAIRE_API_URL"]
        url = f"{base_url}/results/feedObject"
        session = openaire_request_factory()
        res = session.post(url, json=serialized_record, timeout=30)

        # 400/413 are deterministic rejections, retrying never succeeds.
        if res.status_code in (400, 413):
            raise OpenAIREInvalidRecordError(res.status_code, res.text)

        if not res.ok:
            raise OpenAIRERequestError(f"HTTP {res.status_code}: {res.text}")

        beta_base_url = current_app.config.get("OPENAIRE_API_URL_BETA")
        if beta_base_url:
            beta_endpoint = f"{beta_base_url}/results/feedObject"
            res_beta = session.post(beta_endpoint, json=serialized_record, timeout=30)

            if not res_beta.ok:
                # Beta is best-effort, don't raise.
                ctx = {"record_id": record_id, "status_code": res_beta.status_code}
                current_app.logger.warning(
                    "OpenAIRE beta indexing failed for record %(record_id)s (HTTP %(status_code)s).",
                    ctx,
                    extra=ctx,
                )

        current_cache.delete(f"openaire_direct_index:{record_id}")
    except OpenAIREInvalidRecordError as exc:
        # Deterministic rejection: don't retry, drop from the failures cache.
        current_cache.delete(f"openaire_direct_index:{record_id}")
        ctx = {"record_id": record_id, "status_code": exc.status_code}
        current_app.logger.warning(
            "OpenAIRE rejected record %(record_id)s for direct indexing (HTTP %(status_code)s).",
            ctx,
            extra={**ctx, "openaire_response": str(exc)},
        )
    except Exception as exc:
        current_cache.set(
            f"openaire_direct_index:{record_id}", datetime.now(), timeout=-1
        )
        current_app.logger.exception(
            "OpenAIRE direct indexing failed for record %(record_id)s.",
            {"record_id": record_id},
            extra={"record_id": record_id},
        )
        if retry:
            openaire_direct_index.retry(exc=exc)
        else:
            raise exc


@shared_task(
    ignore_result=True,
    max_retries=6,
    default_retry_delay=10 * 60,  # 10 minutes
    rate_limit="100/m",
)
@execute_if_openaire_enabled()
def openaire_delete(record_id=None, retry=True):
    """Delete record from OpenAIRE index.

    :param record_id: Record Metadata UUID.
    :type record_id: str
    """
    try:
        record = records_service.read(system_identity, record_id, include_deleted=True)
        openaire_id = get_openaire_id(record.data)

        session = openaire_request_factory()

        base_url = current_app.config["OPENAIRE_API_URL"]
        res = session.delete(f"{base_url}/result/{openaire_id}")

        if not res.ok:
            raise OpenAIRERequestError(f"HTTP {res.status_code}: {res.text}")

        base_beta_url = current_app.config.get("OPENAIRE_API_URL_BETA")
        if base_beta_url:
            res_beta = session.delete(f"{base_beta_url}/result/{openaire_id}")
            if not res_beta.ok:
                # Beta is best-effort, don't raise.
                ctx = {"record_id": record_id, "status_code": res_beta.status_code}
                current_app.logger.warning(
                    "OpenAIRE beta deletion failed for record %(record_id)s (HTTP %(status_code)s).",
                    ctx,
                    extra=ctx,
                )

        # Remove from failures cache
        current_cache.delete(f"openaire_direct_index:{record_id}")

    except Exception as exc:
        current_cache.set(
            f"openaire_direct_index:{record_id}", datetime.now(), timeout=-1
        )
        current_app.logger.exception(
            "OpenAIRE deletion failed for record %(record_id)s.",
            {"record_id": record_id},
            extra={"record_id": record_id},
        )
        if retry:
            openaire_delete.retry(exc=exc)
        else:
            raise exc


@shared_task
@execute_if_openaire_enabled()
def retry_openaire_failures():
    """Retries failed OpenAIRE indexing/deletion operations."""
    cache = current_cache.cache
    failed_records = cache._write_client.scan_iter(
        cache.key_prefix + "openaire_direct_index:*",
        count=1000,
    )
    for key in failed_records:
        try:
            record_id = key.decode().split("openaire_direct_index:")[1]
            record = records_service.read(
                system_identity, record_id, include_deleted=True
            )
            is_deleted = record.data["deletion_status"]["is_deleted"]

            # If record was deleted, try to remove it from OpenAIRE
            if is_deleted:
                openaire_delete.delay(record_id, retry=False)
            else:
                openaire_direct_index.delay(record_id, retry=False)
        except Exception:
            # Keep going if one record fails, but log so it stays visible.
            current_app.logger.exception(
                "Could not reschedule OpenAIRE retry for cached failure."
            )
            continue
