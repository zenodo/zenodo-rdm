# SPDX-FileCopyrightText: 2023 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Zenodo-RDM release class."""

import json

import yaml
from flask import current_app
from invenio_rdm_records.services.vcs.metadata import RDMReleaseMetadata
from invenio_rdm_records.services.vcs.release import RDMVCSRelease
from invenio_vcs.errors import CustomVCSReleaseNoRetryError
from zenodo_legacy.licenses import legacy_to_rdm

from zenodo_rdm.legacy.deserializers.schemas import LegacySchema
from zenodo_rdm.vcs.schemas import CitationMetadataSchema


class ZenodoReleaseMetadata(RDMReleaseMetadata):
    """Zenodo release metadata class."""

    def load_extra_metadata(self):
        """Get extra metadata for ZenodoRDM."""
        zenodo_json_file_name = ".zenodo.json"
        try:
            override = self.rdm_release.zenodo_json_override
            if override is not None:
                file_data = dict(override)
            elif self.rdm_release.skip_zenodo_json:
                return {}
            else:
                content = self.rdm_release.retrieve_remote_file(zenodo_json_file_name)
                if not content:
                    # File does not exists
                    return {}
                file_data = json.loads(content.decode("utf-8"))
            repo_license = self.rdm_release.generic_repo.license_spdx
            if not file_data.get("license") and repo_license:
                file_data.update({"license": repo_license})
            legacy_data = {"metadata": file_data}
            rdm_data = LegacySchema().load(legacy_data)
            return rdm_data["metadata"]
        except Exception as exc:
            current_app.logger.exception(
                "Extra metadata load failed for file %s: %s",
                zenodo_json_file_name,
                exc,
            )
            raise CustomVCSReleaseNoRetryError(
                message="Extra metadata load failed."
            ) from exc

    def load_citation_file(self, citation_file_name):
        """Return the citation file data, or None if it should be skipped."""
        if self.rdm_release.skip_citation_cff:
            return None
        if not citation_file_name:
            return {}
        content = self.rdm_release.retrieve_remote_file(citation_file_name)
        return yaml.safe_load(content.decode("utf-8")) if content is not None else None

    def load_citation_metadata(self, data):
        """Load citation metadata for Zenodo using legacy->RDM serialization.

        Why overriding the whole method: for Zenodo-RDM, loading the CITATION.cff is not enough. We need to add an extra step
        to convert legacy Zenodo data to RDM.
        """
        if not data:
            return {}

        citation_file_name = current_app.config.get(
            "VCS_CITATION_FILE", "CITATION.cff"
        )

        try:
            repo_license = self.rdm_release.generic_repo.license_spdx
            if not data.get("license") and repo_license:
                data.update({"license": repo_license})
            legacy_data = {"metadata": CitationMetadataSchema().load(data)}
            rdm_data = LegacySchema().load(legacy_data)
            return rdm_data["metadata"]
        except Exception as exc:
            current_app.logger.exception(
                "Citation metadata load failed for file %s: %s",
                citation_file_name,
                exc,
            )
            raise CustomVCSReleaseNoRetryError(
                message="Citation metadata load failed."
            ) from exc


class ZenodoVCSRelease(RDMVCSRelease):
    """Zenodo VCS release class.

    This class adds Zenodo specific metadata.

    Recipe-style overrides (set on an instance before calling ``process_release``)
    let support staff publish releases that would otherwise fail. See the
    "GitHub" section of the support recipes for usage.
    """

    metadata_cls = ZenodoReleaseMetadata

    #: Use this dict as ``.zenodo.json`` content instead of fetching from GitHub.
    zenodo_json_override = None
    #: Fetch metadata files from the repo's default branch instead of the tag.
    metadata_from_head = False
    #: Skip ``.zenodo.json`` entirely (fall through to CITATION.cff or defaults).
    skip_zenodo_json = False
    #: Skip ``CITATION.cff`` entirely.
    skip_citation_cff = False

    def retrieve_remote_file(self, file_name):
        """Retrieve a remote file, honoring ``metadata_from_head``."""
        ref_name = (
            self.generic_repo.default_branch
            if self.metadata_from_head
            else self.generic_release.tag_name
        )
        return self.provider.retrieve_remote_file(
            self.generic_repo.id, ref_name, file_name
        )

    def build_metadata(self):
        """Extracts metadata to create a ZenodoRDM draft."""
        metadata = self.metadata_cls(self)
        output = metadata.default_metadata
        extra_metadata = metadata.extra_metadata

        # If `.zenodo.json` is there use it
        if extra_metadata:
            output.update(extra_metadata)
        # If not check for `CITATION.cff` and use
        else:
            citation_metadata = metadata.citation_metadata
            if citation_metadata:
                output.update(citation_metadata)

        if not output.get("creators"):
            # Get owner from Github API
            owner = self.get_owner()
            if owner:
                output.update({"creators": [owner]})

        # Default to "Unkwnown"
        if not output.get("creators"):
            output.update(
                {
                    "creators": [
                        {
                            "person_or_org": {
                                "type": "personal",
                                "family_name": "Unknown",
                            },
                        }
                    ]
                }
            )
        # Add default license if not yet added
        if not output.get("rights"):
            default_license = "cc-by-4.0"
            if self.generic_repo.license_spdx:
                default_license = self.generic_repo.license_spdx.lower()
            rdm_license = legacy_to_rdm(default_license) or default_license
            output.update({"rights": [{"id": rdm_license}]})
        return output
