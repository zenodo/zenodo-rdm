import tarfile
from datetime import datetime
from io import BytesIO
from pathlib import Path

from flask import current_app
from flask_principal import identity_changed
from invenio_access.permissions import any_user, authenticated_user
from invenio_access.utils import get_identity
from invenio_accounts.proxies import current_datastore
from invenio_app.factory import create_api
from invenio_rdm_records.oai import oai_datacite_etree
from invenio_rdm_records.proxies import current_rdm_records_service as service
from lxml import etree

USER_ID = "CHANGEME"
EXPORT_DIR = Path("/tmp/export")


def identity_for(id_or_email):
    idty = get_identity(current_datastore.get_user(id_or_email))
    with current_app.test_request_context():
        identity_changed.send(current_app, identity=idty)
        # Needs to be added manually
        idty.provides.add(authenticated_user)
        idty.provides.add(any_user)
    return idty


def export_datacite():
    # Change this to the user ID or email you want to use
    idty = identity_for(USER_ID)

    EXPORT_DIR.mkdir(exist_ok=True, parents=True)
    tar_path = f"{EXPORT_DIR}/zenodo-{datetime.today().isoformat()}.tar.gz"
    failed_path = f"{EXPORT_DIR}/failed.txt"
    with tarfile.open(tar_path, "w|gz") as tar, open(failed_path, "w") as failed:
        res = service.scan(idty, params={"allversions": True})
        for idx, record in enumerate(res.hits):
            if idx % 1000 == 0:
                print(datetime.now().isoformat(), idx)
            record_id = record.get("id")
            if not record_id:
                continue

            try:
                oai_etree = oai_datacite_etree(None, {"_source": record})
                xml_bytes = etree.tostring(
                    oai_etree,
                    xml_declaration=True,
                    encoding="UTF-8",
                )

                tar_info = tarfile.TarInfo(f"{record_id}.xml")
                file_content = BytesIO()
                file_content.name = f"{record_id}.xml"
                file_content.write(xml_bytes)
                file_content.seek(0)
                tar_info.size = len(xml_bytes)
                tar.addfile(tar_info, fileobj=file_content)
            except Exception as e:
                print(f"Error serializing {record_id}: {e}")
                failed.write(f"{record_id}\n")


if __name__ == "__main__":
    with create_api().app_context():
        export_datacite()
