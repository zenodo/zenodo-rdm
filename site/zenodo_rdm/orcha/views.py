from datetime import datetime, timedelta, timezone

import jwt
import requests
from cryptography.hazmat.primitives import serialization
from flask import (
    Blueprint,
    Response,
    abort,
    current_app,
    g,
    jsonify,
    request,
    stream_with_context,
    url_for,
)
from invenio_access.permissions import system_identity
from invenio_files_rest.errors import InvalidOperationError
from invenio_rdm_records.proxies import current_rdm_records
from invenio_records_resources.services.errors import PermissionDeniedError

from .client import OrchaClient

blueprint = Blueprint("orcha", __name__)


def _orcha_client():
    return OrchaClient(
        key_path=current_app.config["ZENODO_ORCHA_KEY_PATH"],
        key_id=current_app.config["ZENODO_ORCHA_KID"],
        tenant=current_app.config["ZENODO_ORCHA_TENANT"],
        base_url=current_app.config["ZENODO_ORCHA_URL"],
        public_url=current_app.config.get("ZENODO_ORCHA_PUBLIC_URL"),
        ssl_verify=current_app.config.get("ZENODO_ORCHA_SSL_VERIFY", True),
    )


def _record_file(pid_value, key=None, identity=None):
    service = current_rdm_records.records_service
    identity = identity if identity is not None else g.identity
    draft = service.read_draft(identity, pid_value)._record

    if not (draft.files and draft.files.entries):
        raise InvalidOperationError(description="Draft has no files")

    file_key = key or next(iter(draft.files.entries))
    if file_key not in draft.files.entries:
        raise InvalidOperationError(description="Draft file does not exist")

    return draft, file_key, draft.files[file_key]


def _file_download_url(pid_value, orcha):
    permission = current_app.config["ZENODO_ORCHA_PERMISSION"]
    if not permission():
        raise PermissionDeniedError()

    draft, first_file_name, _ = _record_file(pid_value)
    service = current_rdm_records.records_service
    service.require_permission(g.identity, "manage", record=draft)

    return url_for(
        "orcha.download_orcha_file",
        pid_value=pid_value,
        key=first_file_name,
        token=_file_download_token(orcha, pid_value, first_file_name),
        _external=True,
    )


@blueprint.route("/uploads/<pid_value>/orcha", methods=["POST"])
def get_workflow_stream_url(pid_value):
    if pid_value in {None, "", "null", "undefined"}:
        return jsonify(
            {"error": "Draft must be saved before extracting metadata."}
        ), 400

    orcha = _orcha_client()
    payload = {
        "workflow_type": "extract_metadata",
        "params": {"url": _file_download_url(pid_value, orcha)},
    }

    try:
        response = orcha.trigger_workflow(payload, _workflow_token(orcha))
        workflow_id = response["public_id"]
        return (
            jsonify(
                {
                    "workflowId": workflow_id,
                    "streamUrl": orcha.stream_url(
                        workflow_id,
                        _workflow_token(orcha, workflow_id),
                    ),
                }
            ),
            200,
        )
    except requests.Timeout:
        return jsonify({"error": "Workflow service timed out."}), 504
    except requests.ConnectionError:
        return jsonify({"error": "Workflow service unavailable."}), 503
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code in {401, 403}:
            return jsonify({"error": "Workflow service authorization failed."}), 502
        return jsonify({"error": "Failed to trigger workflow"}), 502


def _workflow_token(client, workflow_id=None, expiry=timedelta(minutes=30)):
    return jwt.encode(
        {
            "workflow_id": workflow_id or "*",
            "iss": client.tenant,
            "exp": datetime.now(timezone.utc) + expiry,
        },
        client.private_key,
        algorithm="RS256",
        headers={"kid": client.key_id},
    )


def _file_download_token(client, pid_value, key, expiry=timedelta(minutes=30)):
    return jwt.encode(
        {
            "scope": "orcha:file-download",
            "pid": pid_value,
            "key": key,
            "iss": client.tenant,
            "exp": datetime.now(timezone.utc) + expiry,
        },
        client.private_key,
        algorithm="RS256",
        headers={"kid": client.key_id},
    )


def _public_key(private_key):
    if isinstance(private_key, str):
        private_key = private_key.encode()
    return serialization.load_pem_private_key(private_key, password=None).public_key()


def _verify_file_download_token(client, pid_value, key):
    token = request.args.get("token")
    if not token:
        abort(401)

    try:
        claims = jwt.decode(
            token,
            _public_key(client.private_key),
            algorithms=["RS256"],
            issuer=client.tenant,
        )
    except jwt.ExpiredSignatureError:
        abort(401)
    except jwt.InvalidTokenError:
        abort(401)

    if (
        claims.get("scope") != "orcha:file-download"
        or claims.get("pid") != pid_value
        or claims.get("key") != key
    ):
        abort(403)


@blueprint.route("/uploads/<pid_value>/orcha/files/<path:key>", methods=["GET"])
def download_orcha_file(pid_value, key):
    orcha = _orcha_client()
    _verify_file_download_token(orcha, pid_value, key)
    _, _, record_file = _record_file(pid_value, key=key, identity=system_identity)
    return record_file.object_version.send_file()


@blueprint.route("/orcha-proxy/<path:subpath>", methods=["GET"])
def orcha_proxy(subpath):
    orcha = _orcha_client()
    upstream_url = f"{orcha.base_url}/{subpath}"
    upstream = requests.get(
        upstream_url,
        params=request.args,
        stream=True,
        timeout=(10, None),
        verify=orcha.ssl_verify,
    )

    def generate():
        try:
            for chunk in upstream.iter_content(chunk_size=None):
                if chunk:
                    yield chunk
        finally:
            upstream.close()

    headers = {
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
    }
    return Response(
        stream_with_context(generate()),
        status=upstream.status_code,
        headers=headers,
        mimetype=upstream.headers.get("Content-Type", "text/event-stream"),
    )
