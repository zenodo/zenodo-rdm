# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Redirector functions and rules."""

from urllib.parse import urlencode

from flask import abort, current_app, request, url_for
from invenio_app_rdm.redirector.resource import RedirectorConfig, RedirectorResource
from invenio_communities import current_communities
from invenio_records_resources.services.base.config import FromConfig
from invenio_requests.proxies import current_requests_service

ZENODO_TYPE_SUBTYPE_LEGACY = {
    "publications": "publication",
    "books": "publication.book",
    "books-sections": "publication.section",
    "conference-papers": "publication.conferencepaper",
    "journal-articles": "publication.article",
    "patents": "publication.patent",
    "preprints": "publication.preprint",
    "deliverable": "publication.deliverable",
    "milestone": "publication.milestone",
    "proposal": "publication.proposal",
    "reports": "publication.report",
    "theses": "publication.thesis",
    "technical-notes": "publication.technicalnote",
    "working-papers": "publication.workingpaper",
    "other-publications": "publication.other",
    "posters": "poster",
    "presentations": "presentation",
    "datasets": "dataset",
    "images": "image",
    "figures": "image.figure",
    "drawings": "image.drawing",
    "diagrams": "image.diagram",
    "photos": "image.photo",
    "other-images": "image.other",
    "videos": "video",
    "software": "software",
    "lessons": "lesson",
    "physicalobject": "physicalobject",
    "workflows": "workflow",
    "other": "other",
}


def communities_detail_view_function():
    """Implements redirector view function for communities detail.

    The following routes are redirected as follows:
        - /communities/about/<id>/ -> GET /communities/<pid_value>
        - /collection/user-<id> -> GET /communities/<pid_value>

    :return: url for the view 'invenio_app_rdm_communities.communities_detail'
    :rtype: str
    """
    _id = request.view_args["id"]
    values = {"pid_value": _id}
    target = url_for("invenio_app_rdm_communities.communities_detail", **values)
    return target


def communities_settings_view_function():
    """Implements redirector view function for communities settings.

    The following routes are redirected as follows:
        - /communities/<community_id>/edit -> GET /communities/<community_id>/settings

    :return: url for the view 'invenio_communities.communities_settings'
    :rtype: str
    """
    _id = request.view_args["community_id"]
    values = {"pid_value": _id}
    target = url_for("invenio_communities.communities_settings", **values)
    return target


def communities_requests_view_function():
    """Implements redirector view function for communities requests.

    The following routes are redirected as follows:
        - /communities/<community_id>/curate -> GET /communities/<community_id>/settings

    :return: url for the view 'invenio_communities.communities_requests'
    :rtype: str
    """
    _id = request.view_args.get("id", request.view_args["community_id"])
    values = {"pid_value": _id}
    target = url_for("invenio_communities.communities_requests", **values)
    return target


def communities_records_search():
    """Implements redirector view function for communities records search.

    The following routes are redirected as follows:
        - /communities/<string:community_id>/search -> GET /communities/<pid_value>/q=<query>

    :return: url for the view 'invenio_communities.communities_detail'
    :rtype: str
    """
    _id = request.view_args.get("id", request.view_args["community_id"])
    values = {"pid_value": _id}
    _q = request.args.get("q", "")
    url = url_for("invenio_app_rdm_communities.communities_detail", **values)
    target = f"{url}?q={_q}"
    return target


def search_view_function():
    """Implements redirector view function for search ui.

    The following routes are redirected as follows:
        - /collection/<type> -> GET /search?q=<type>

    :return: url for the view 'invenio_search_ui.search'
    :rtype: str
    """
    _type = request.view_args["type"]
    legacy_value = ZENODO_TYPE_SUBTYPE_LEGACY.get(_type)
    values = {"q": f"metadata.resource_type.id:{legacy_value}"}
    target = url_for("invenio_search_ui.search", **values)
    return target


def deposit_view_function():
    """Implements redirector view function for deposit edit.

    The following routes are redirected as follows:
        - /deposit/<pid_value>  -> GET /uploads/<pid_value>

    :return: url for the view 'invenio_app_rdm_records.deposit_edit'
    :rtype: str
    """
    values = request.view_args
    target = url_for("invenio_app_rdm_records.deposit_edit", **values)
    return target


def record_view_function():
    """Implements redirector view function for record detail.

    The following routes are redirected as follows:
        - /record/<pid_value>', -> GET /records/<pid_value>

    :return: url for the view 'invenio_app_rdm_records.record_detail'
    :rtype: str
    """
    values = request.view_args
    target = url_for("invenio_app_rdm_records.record_detail", **values)
    return target


def record_export_view():
    """Implements redirector view function for record export.

    The following routes are redirected as follows:
        -  /record/<pid_value>/export/<export_format> -> GET /records/<pid_value>/export/<export_format>

    :return: url for the view 'invenio_app_rdm_records.record_export'
    :rtype: str
    """
    values = request.view_args
    target = url_for("invenio_app_rdm_records.record_export", **values)
    return target


def legacy_record_export_view():
    """Implements redirector view function for legacy values of record export.

    The following routes are redirected as follows:
        -  /records/<pid_value>/export/<legacy_export_format> -> GET /record/<pid_value>/export/<export_format>

    :return: url for the view 'invenio_app_rdm_records.record_export'
    :rtype: str
    """
    formats = current_app.config["ZENODO_RECORD_EXPORTERS_LEGACY"]
    args = request.view_args
    legacy_value = request.path.split("/")[-1]

    values = {"export_format": formats[legacy_value], "pid_value": args["pid_value"]}
    target = url_for("invenio_app_rdm_records.record_export", **values)
    return target


def record_file_download_view():
    """Implements redirector view function for record export.

    The following routes are redirected as follows:
        -  /record/<pid_value>/files/<filename> -> GET /records/<pid_value>/files/<filename>

    :return: url for the view 'invenio_app_rdm_records.record_file_download'
    :rtype: str
    """
    values = request.view_args
    target = url_for("invenio_app_rdm_records.record_file_download", **values)
    return target


def redirect_record_file_preview_view():
    """Implements redirector view function for record file preview.

    The following routes are redirected as follows:
        -  /record/<pid_value>/preview/<filename> -> /records/<pid_value>/preview/<filename>

    :return: url for the view 'invenio_app_rdm_records.record_file_preview'
    :rtype: str
    """
    values = request.view_args
    target = url_for("invenio_app_rdm_records.record_file_preview", **values)
    return target


def redirect_deposit_own_view():
    """Implements redirector view function for user uploads.

    The following routes are redirected as follows:
        -  /deposit -> GET /me/uploads

    :return: url for the view 'invenio_app_rdm_users.uploads'
    :rtype: str
    """
    _q = "&is_published=false"
    url = url_for("invenio_app_rdm_users.uploads")
    target = f"{url}?q={_q}"
    return target


def redirect_deposit_new_view():
    """Implements redirector view function for deposit creation.

    The following routes are redirected as follows:
        -  /deposit/new?c=<slug> -> GET /uploads/new?community=<slug>

    :return: url for the view 'invenio_app_rdm_records.deposit_create'
    :rtype: str
    """
    values = {}
    community_slug = request.args.get("c", None)
    if community_slug:
        values = {"community": community_slug}
    target = url_for("invenio_app_rdm_records.deposit_create", **values)
    return target


def redirect_record_thumbnail_view():
    """Redirect legacy record thumbnail URL.

    The following routes are redirected as follows:
        - /record/<pid_value>/thumb<size> -> /records/<pid_value>/thumb<size>
    """
    return url_for("invenio_app_rdm_records.record_thumbnail", **request.view_args)


def redirect_formats_to_media_files_view():
    """Redirect formats to media files URLs.

    The following routes are redirected as follows:
        - /record/<pid_value>/formats?mimetype=<filename> -> GET /records/<pid_value>/media-files/<filename>

    :return: url for the view 'invenio_app_rdm_records.record_media_file_download'
    :rtype: str
    """
    values = request.view_args
    filename = request.args.get("mimetype", None)
    values["filename"] = filename

    target = url_for("invenio_app_rdm_records.record_media_file_download", **values)
    return target


def redirect_access_request():
    """Redirect formats to media files URLs.

    /account/settings/sharedlinks/accessrequest/<number>/ -> GET /access/requests/<request_pid_value>

    :return: url for the view 'invenio_app_rdm_requests.read_request'
    :rtype: str
    """
    number = request.view_args["number"]
    RequestModel = current_requests_service.record_cls.model_cls

    request_model = RequestModel.query.filter_by(number=number).one_or_none()
    if not request_model:
        abort(404)
    return url_for(
        "invenio_app_rdm_requests.read_request",
        request_pid_value=str(request_model.id),
    )


####### Zenodo REST API redirections #######################


def redirect_records_search_slash():
    """Redirect /api/records/ to /api/records retaining search args."""
    values = request.args
    target = url_for("records.search", **values)
    return target


def redirect_licenses():
    """Redirect /api/licenses/ to /api/vocabularies/licenses retaining search args."""
    values = request.args
    target = url_for("vocabularies.search", type="licenses", **values)
    return target


class ZenodoRedirectorConfig(RedirectorConfig):
    """Zenodo REST API redirector config."""

    # Blueprint configuration
    blueprint_name = "zenodo_api_redirector"

    rules = FromConfig("API_REDIRECTOR_RULES", {})


def create_blueprint(app):
    """Creates a blueprint for the redirector resource."""
    resource = RedirectorResource(ZenodoRedirectorConfig.build(app))
    blueprint = resource.as_blueprint()
    return blueprint
