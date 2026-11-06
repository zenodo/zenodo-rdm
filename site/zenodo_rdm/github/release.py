# SPDX-FileCopyrightText: 2023 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Zenodo-RDM release class."""

import json
from functools import cached_property

import github3
from flask import current_app
from invenio_github.errors import CustomGitHubMetadataError
from invenio_rdm_records.services.github.metadata import RDMReleaseMetadata
from invenio_rdm_records.services.github.release import RDMGithubRelease
from zenodo_legacy.licenses import legacy_to_rdm

from zenodo_rdm.github.schemas import CitationMetadataSchema
from zenodo_rdm.legacy.deserializers.schemas import LegacySchema


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
                file_data = json.loads(content.decoded.decode("utf-8"))
            if not file_data.get("license") and self.repo_license:
                file_data.update({"license": self.repo_license})
            legacy_data = {"metadata": file_data}
            rdm_data = LegacySchema().load(legacy_data)
            return rdm_data["metadata"]
        except Exception as exc:
            current_app.logger.exception(str(exc))
            raise CustomGitHubMetadataError(
                file=zenodo_json_file_name, message="Extra metadata load failed."
            )

    def load_citation_file(self, citation_file_name):
        """Return the citation file data, or None if it should be skipped."""
        if self.rdm_release.skip_citation_cff:
            return None
        return super().load_citation_file(citation_file_name)

    def load_citation_metadata(self, data):
        """Load citation metadata for Zenodo using legacy->RDM serialization.

        Why overriding the whole method: for Zenodo-RDM, loading the CITATION.cff is not enough. We need to add an extra step
        to convert legacy Zenodo data to RDM.
        """
        if not data:
            return {}

        citation_file_name = current_app.config.get(
            "GITHUB_CITATION_FILE", "CITATION.cff"
        )

        try:
            if not data.get("license") and self.repo_license:
                data.update({"license": self.repo_license})
            legacy_data = {"metadata": CitationMetadataSchema().load(data)}
            rdm_data = LegacySchema().load(legacy_data)
            return rdm_data["metadata"]
        except Exception as exc:
            exc_str = str(exc)
            current_app.logger.exception(exc_str)
            raise CustomGitHubMetadataError(
                file=citation_file_name, message=f"Citation metadata load failed: {exc_str}"
            )


class ZenodoGithubRelease(RDMGithubRelease):
    """Zenodo Github release class.

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

    @cached_property
    def _default_branch(self):
        """Resolve the repository's default branch via the GitHub API."""
        owner = self.repository_payload["owner"]["login"]
        name = self.repository_payload["name"]
        return self.gh.api.repository(owner, name).default_branch

    def retrieve_remote_file(self, file_name):
        """Retrieve a remote file, honoring ``metadata_from_head``."""
        if not self.metadata_from_head:
            return super().retrieve_remote_file(file_name)
        owner = self.repository_payload["owner"]["login"]
        name = self.repository_payload["name"]
        try:
            return self.gh.api.repository(owner, name).file_contents(
                path=file_name, ref=self._default_branch
            )
        except github3.exceptions.NotFoundError:
            return None

    @property
    def metadata(self):
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
            if metadata.repo_license:
                default_license = metadata.repo_license.lower()
            rdm_license = legacy_to_rdm(default_license) or default_license
            output.update({"rights": [{"id": rdm_license}]})
        return output
