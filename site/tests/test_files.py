# SPDX-FileCopyrightText: 2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Test files offloading."""

from urllib.parse import quote

import pytest

from zenodo_rdm.files import EOSFilesOffload, LocalFilesOffload, storage_factory


def test_storage_factory_picks_class_by_uri(app):
    """EOS URIs keep the EOS storage, local paths get the local one."""
    eos = storage_factory(fileurl="root://eosmedia.cern.ch//eos/x/data", size=1)
    local = storage_factory(fileurl="/opt/invenio/var/instance/images/x.ptif", size=1)
    assert type(eos) is EOSFilesOffload
    assert type(local) is LocalFilesOffload


@pytest.mark.parametrize(
    "eos_enabled,local_enabled,offloaded",
    [
        # The EOS offload flag has no effect on local files
        (True, False, False),
        (False, True, True),
        (False, False, False),
    ],
)
def test_local_file_send(
    app,
    tmp_path,
    set_app_config_fn_scoped,
    eos_enabled,
    local_enabled,
    offloaded,
):
    """Local files are offloaded to nginx only when local offload is enabled."""
    set_app_config_fn_scoped(
        {
            "FILES_REST_XSENDFILE_ENABLED": True,
            "ZENODO_EOS_OFFLOAD_ENABLED": eos_enabled,
            "ZENODO_LOCAL_OFFLOAD_ENABLED": local_enabled,
            "ZENODO_LOCAL_OFFLOAD_REDIRECT_BASE_PATH": "/_local_files",
        }
    )
    path = tmp_path / "my poster@v1?.pdf.ptif"
    path.write_bytes(b"ptif-data")

    storage = storage_factory(fileurl=str(path), size=path.stat().st_size)
    with app.test_request_context():
        res = storage.send_file(path.name)
        res.direct_passthrough = False

        if offloaded:
            assert res.headers["X-Accel-Redirect"] == f"/_local_files{quote(str(path))}"
            assert res.get_data() == b""
        else:
            assert "X-Accel-Redirect" not in res.headers
            assert res.get_data() == b"ptif-data"
