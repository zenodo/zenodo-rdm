from invenio_rdm_records.resources.serializers.schema import \
    MARCXMLSchema as BaseMARCXMLSchema
from marshmallow import fields, missing


class MARCXMLSchema(BaseMARCXMLSchema):
    """Schema for records in MARC."""

    @post_dump(pass_original=True)
    def add_legacy_fields(self, result, original, **kwargs):
        """Dump identifiers."""
        meeting_information = fields.Method("get_meeting_info", data_key="711  ")

    def get_meeting_info(self, obj):
        """Get host information.

        Contains related identifiers as well as the parent DOI.
        """
        host_information = []

        # Related identifiers
        related_identifiers = obj["metadata"].get("related_identifiers", [])
        for identifier in related_identifiers:
            related_identifier = {
                "a": identifier["identifier"],
                "i": identifier["relation_type"]["title"]["en"],
                "n": identifier["scheme"],
            }
            host_information.append(related_identifier)

        # Parent DOI
        parent_pids = obj["parent"].get("pids", {})
        for key, value in parent_pids.items():
            if key == "doi":
                parent_doi = {
                    "a": value["identifier"],  # identifier
                    "i": "isVersionOf",  # relation type with parent is "isVersionOf"
                    "n": "doi",  # scheme
                }
                host_information.append(parent_doi)
                break

        return host_information or missing
