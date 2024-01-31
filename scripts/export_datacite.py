from io import BytesIO
from datetime import datetime
import tarfile
from flask import current_app
from lxml import etree
from invenio_rdm_records.oai import oai_datacite_etree
from invenio_rdm_records.proxies import current_rdm_records_service as service
from invenio_access.permissions import any_user, authenticated_user
from flask_principal import identity_changed
from invenio_access.utils import get_identity
from invenio_accounts.proxies import current_datastore


def identity_for(id_or_email):
    idty = get_identity(current_datastore.get_user(id_or_email))
    with current_app.test_request_context():
        identity_changed.send(current_app, identity=idty)
        # Needs to be added manually
        idty.provides.add(authenticated_user)
        idty.provides.add(any_user)
    return idty


# Change this to the user ID or email you want to use
idty = identity_for(1)

tar_path = f"zenodo-{datetime.today().isoformat()}.tar.gz"

with tarfile.open(tar_path, "w|gz") as tar, open("failed.txt", "w") as failed:
    res = service.scan(idty)
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
