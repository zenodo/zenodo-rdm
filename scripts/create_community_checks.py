# SPDX-FileCopyrightText: 2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Script to create metadata checks for communities.

Usage:

.. code-block:: shell

    source .venv/bin/activate
    invenio shell create_community_checks.py
"""

from copy import deepcopy

from invenio_access.permissions import system_identity
from invenio_checks.models import CheckConfig, Severity
from invenio_communities.proxies import current_communities
from invenio_db import db
from invenio_search.api import dsl
from werkzeug.local import LocalProxy

community_service = LocalProxy(lambda: current_communities.service)

### NASA Heliophysics community
# https://sandbox.zenodo.org/communities/nasaheliorepository/
NASA_HELIO_RULES = {
    "rules": [
        {
            "id": "creators:identifier",
            "title": "Creator Identifiers",
            "message": "At least one creator should have a persistent identifier (ORCID)",
            "description": 'You should provide persistent identifiers (ORCID) for at least one creator.',
            "level": "error",
            "condition": {
                "type": "list",
                "operator": "exists",
                "path": "metadata.creators",
                "predicate": {},
            },
            "checks": [
                {
                    "type": "list",
                    "operator": "any",
                    "path": "metadata.creators",
                    "predicate": {
                        "type": "list",
                        "operator": "exists",
                        "path": "person_or_org.identifiers",
                        "predicate": {
                            "type": "comparison",
                            "left": {"type": "field", "path": "scheme"},
                            "operator": "==",
                            "right": "orcid",
                        },
                    },
                }
            ],
        },
        {
            "id": "title:length",
            "title": "Title length",
            "message": "Title length must be between 5 and 300 characters",
            "description": "The title should be at least 5 characters long and should not exceed 300 characters.",
            "level": "error",
            "checks": [
                {
                    "type": "comparison",
                    "left": {"type": "field", "path": "metadata.title"},
                    "operator": "min",
                    "right": 5
                },
                {
                    "type": "comparison",
                    "left": {"type": "field", "path": "metadata.title"},
                    "operator": "max",
                    "right": 300
                },
            ],
        },
        {
            "id": "description:length",
            "title": "Description length",
            "message": "Description length must be between 50 and 5000 characters",
            "description": "The description should be at least 50 characters long and should not exceed 5000 characters.",
            "level": "error",
            "checks": [
                {
                    "type": "comparison",
                    "left": {"type": "field", "path": "metadata.description"},
                    "operator": "min",
                    "right": 50
                },
                {
                    "type": "comparison",
                    "left": {"type": "field", "path": "metadata.description"},
                    "operator": "max",
                    "right": 5000
                },
            ],
        },
        {
            "id": "subjects:length",
            "title": "Number of subjects",
            "message": "At least 3 keywords or subjects are required",
            "description": 'The number of keywords or subjects must be at least 3, with at least one subject from the <a href="https://astrothesaurus.org/concept-select/" target="_blank" rel="noopener noreferrer">UAT</a>',
            "level": "error",
            "checks": [
                {
                    "type": "comparison",
                    "left": {"type": "field", "path": "metadata.subjects"},
                    "operator": "min",
                    "right": 3
                },
            ],
        },
        {
            "id": "funding",
            "title": "Funding information",
            "message": "Submissions must include a grant or award from the NASA Heliophysics Division. Custom awards require a number of at least 10 characters and a mandatory title.",
            "description": 'The NASA Heliophysics Repository only accepts submissions associated with the <a href="https://ror.org/03myraf72" target="_blank" rel="noopener noreferrer">Heliophysics Science Division (03myraf72)</a>. Additional grants must have a number of at least 10 characters and a mandatory title.'
            "level": "error",
            "checks": [
                {
                    "type": "list",
                    "operator": "any",
                    "path": "metadata.funding",
                    "predicate": {
                        "type": "comparison",
                        "left": {"type": "field", "path": "funder.id"},
                        "operator": "==",
                        "right": "03myraf72",
                    },
                },
                {
                    "type": "list",
                    "operator": "all",
                    "path": "metadata.funding",
                    "predicate": {
                        "type": "comparison",
                        "left": {"type": "field", "path": "award.number"},
                        "operator": "min",
                        "right": 10,
                    },
                },
                {
                    "type": "list",
                    "operator": "all",
                    "path": "metadata.funding",
                    "predicate": {
                        "type": "comparison",
                        "left": {"type": "field", "path": "award.title"},
                        "operator": "min",
                        "right": 1,
                    },
                }
            ],
        },
        {
            "id": "license:exists",
            "title": "Record license",
            "message": "All submissions must specify licensing terms",
            "description": 'A submission must specify the licensing terms.',
            "level": "error",
            "checks": [
                {
                    "type": "list",
                    "operator": "exists",
                    "path": "metadata.rights",
                    "predicate": {},
                }
            ],
        },
        {
            "id": "license:cc0/dataset",
            "title": "Dataset License",
            "message": "Datasets should have CC0-1.0 license",
            "description": 'Datasets must be available under the latest Creative Commons Zero v1.0 Universal (CC0-1.0).',
            "level": "info",
            "condition": {
                "type": "logical",
                "operator": "and",
                "expressions": [
                    {
                        "type": "comparison",
                        "left": {"type": "field", "path": "metadata.resource_type.id"},
                        "operator": "==",
                        "right": "dataset",
                    },
                    {
                        "type": "list",
                        "operator": "exists",
                        "path": "metadata.rights",
                        "predicate": {},
                    },
                ],
            },
            "checks": [
                {
                    "type": "list",
                    "operator": "any",
                    "path": "metadata.rights",
                    "predicate": {
                        "type": "comparison",
                        "left": {"type": "field", "path": "id"},
                        "operator": "in",
                        "right": [
                            "cc-zero",
                        ],
                    },
                }
            ],
        },
        {
            "id": "software:url",
            "title": "Software URL requirement",
            "message": "A valid URL is required for software submissions",
            "description": "When submitting software, a valid and accessible URL must be provided in the 'codeRepository' field.",
            "level": "error",
            "condition": {
                "type": "comparison",
                "left": {"type": "field", "path": "metadata.resource_type.id"},
                "operator": "==",
                "right": "software",
            },
            "checks": [
                {
                    "type": "comparison",
                    "left": {"type": "field", "path": "custom.code:codeRepository"},
                    "operator": "min",
                    "right": 1
                },
            ],
        },
    ]
}

FILE_FORMAT_CONFIG = {
    "closed_format_description": "Using closed or proprietary formats hinders reusability and preservation of published files. <a href='https://zenodo.org/communities/{slug}/curation-policy' target='_blank' >Learn more</a>",
}

def create_metadata_checks(config, comm):
    existing_check = CheckConfig.query.filter_by(
        community_id=comm.id, check_id="metadata"
    ).one_or_none()
    if existing_check:  # If it exists, update it
        existing_check.params = config
    else:  # ...create it
        check_config = CheckConfig(
            community_id=comm.id,
            check_id="metadata",
            params=config,
            severity=Severity.INFO,
            enabled=True,
        )
        db.session.add(check_config)
    db.session.commit()
    print(f"Metadata checks created/updated successfully for community {comm.slug}.")


def create_file_format_checks(config, comm):
    existing_check = CheckConfig.query.filter_by(
        community_id=comm.id, check_id="file_formats"
    ).one_or_none()

    ffconfig = deepcopy(FILE_FORMAT_CONFIG)
    ffconfig["closed_format_description"].format(slug=comm.slug)

    if existing_check:  # If it exists, update it
        existing_check.params = ffconfig
    else:  # ...create it
        check_config = CheckConfig(
            community_id=comm.id,
            check_id="file_formats",
            params=ffconfig,
            severity=Severity.INFO,
            enabled=True,
        )
        db.session.add(check_config)
    db.session.commit()
    print(
        f"File format checks created/updated successfully for community {comm.slug}."
    )

def create_checks(slug, config):
    comm = community_service.record_cls.pid.resolve(slug)
    create_metadata_checks(config, comm)
    create_file_format_checks(config, comm)
    print(f"{slug} community checks created/updated successfully.")


if __name__ == "__main__":
    create_checks("nasaheliorepository", NASA_HELIO_RULES)

    # Testing
    # creators
    #record = {"metadata": {"type": "article", "creators": [{"person_or_org": {"given_name": "Rossi"}}]}}  # fail: 1 creator, no ORCID
    #record = {"metadata": {"type": "article", "creators": [{"person_or_org": {"given_name": "Rossi", "identifiers": [{"identifier": "random orcid", "scheme": "orcid"}]}}]}}  # success: 1 creator, with ORCID
    #record = {"metadata": {"type": "article", "creators": [{"person_or_org": {"given_name": "Rossi", "identifiers": [{"identifier": "random orcid", "scheme": "orcid"}]}},{"person_or_org": {"given_name": "Rossi2"}}]}}  # success: 2 creators, 1 with ORCID
    # title 5 < chars < 300
    #record = {"metadata": {"type": "article", "title": "My title", "creators": [{"person_or_org": {"given_name": "Rossi", "identifiers": [{"identifier": "random orcid", "scheme": "orcid"}]}}]}}  # fail: title too short
    # min. 3 subjects
    #record = {"metadata": {"type": "article", "title": "My title", "description": "a"*100, "subjects": [{"subject": "website"}]}}
    # funder: wrong id
    # record = {"metadata": {"type": "article", "title": "My title", "description": "a"*100, "subjects": [{"subject": "website"}, {"subject": "website1"}, {"subject": "website2"}],
    #    "funding": [{"funder": {"id": "03myraf72wrong"}}]}}
    # funder: correct id, award number less than 10 chars
    # record = {"metadata": {"type": "article", "title": "My title", "description": "a"*100, "subjects": [{"subject": "website"}, {"subject": "website1"}, {"subject": "website2"}],
    #    "funding": [{"funder": {"id": "03myraf72"}, "award": {"number": "aaa"}}]}}
    # funder: correct id, award title too short
    # record = {"metadata": {"type": "article", "title": "My title", "description": "a"*100, "subjects": [{"subject": "website"}, {"subject": "website1"}, {"subject": "website2"}],
    #    "funding": [{"funder": {"id": "03myraf72"}, "award": {"number": "NNH24ZDA001N-HARD"}}]}}
    # record = {"metadata": {"type": "article", "title": "My title", "description": "a"*100, "subjects": [{"subject": "website"}, {"subject": "website1"}, {"subject": "website2"}],
    #    "funding": [{"funder": {"id": "03myraf72"}, "award": {"number": "NNH24ZDA001N-HARD", "title": ""}}]}}
    # funder: correct
    # record = {"metadata": {"type": "article", "title": "My title", "description": "a"*100, "subjects": [{"subject": "website"}, {"subject": "website1"}, {"subject": "website2"}],
    #     "funding": [{"funder": {"id": "03myraf72"}, "award": {"number": "NNH24ZDA001N-HARD", "title": "my title"}}]}}
    # for config in NASA_HELIO_RULES["rules"]:
    #     rule = RuleParser.parse(config)
    #     result = rule.evaluate(record)
    #     assert result.success is True
