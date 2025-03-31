# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Zenodo-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Script to create metadata checks for the EC community and sub-communities.

Usage:

.. code-block:: shell

    invenio shell ec_create_checks.py
"""

from copy import deepcopy

from invenio_access.permissions import system_identity
from invenio_checks.models import CheckConfig, Severity
from invenio_communities.proxies import current_communities
from invenio_db import db
from invenio_search.api import dsl
from werkzeug.local import LocalProxy

community_service = LocalProxy(lambda: current_communities.service)


EU_RULES = {
    "rules": [
        {
            "id": "journal:title/publication",
            "title": "Journal Information",
            "message": "Journal articles must specify the publishing venue",
            "description": 'To comply with Horizon Europe\'s open science requirements, peer-reviewed scientific publications must specify the publishing venue (e.g. journal) it was published in. <a href="/communities/eu/pages/open-science" target="_blank">Learn more</a>',
            "level": "error",
            "condition": {
                "type": "comparison",
                "left": {"type": "field", "path": "metadata.resource_type.id"},
                "operator": "==",
                "right": "publication-article",
            },
            "checks": [
                {
                    "type": "comparison",
                    "left": {
                        "type": "field",
                        "path": "custom_fields.journal:journal.title",
                    },
                    "operator": "!=",
                    "right": "",
                }
            ],
        },
        {
            "id": "license:exists",
            "title": "Record license",
            "message": "All submissions must specify licensing terms",
            "description": 'To comply with Horizon Europe\'s open science requirements, a submission must specify the licensing terms. <a href="/communities/eu/pages/open-science" target="_blank">Learn more</a>',
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
            "id": "license:cc-by/publication",
            "title": "Journal Article License",
            "message": "Journal articles should have a CC-BY license or license with equivalent rights",
            "description": 'To comply with Horizon Europe\'s open science requirements, peer-reviewed scientific publications must be available under the latest Creative Commons Attribution International license (CC-BY) or a license with equivalent rights. Please ensure the license you have selected provide the same rights as CC-BY. <a href="/communities/eu/pages/open-science" target="_blank">Learn more</a>',
            "level": "info",
            "condition": {
                "type": "logical",
                "operator": "and",
                "expressions": [
                    {
                        "type": "comparison",
                        "left": {"type": "field", "path": "metadata.resource_type.id"},
                        "operator": "==",
                        "right": "publication-article",
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
                            "cc-by-1.0",
                            "cc-by-2.0",
                            "cc-by-2.5",
                            "cc-by-3.0",
                            "cc-by-3.0-at",
                            "cc-by-3.0-us",
                            "cc-by-4.0",
                        ],
                    },
                }
            ],
        },
        {
            "id": "license:cc-by-nc-nd/book",
            "title": "Book License",
            "message": "Books should have a CC-BY, CC-BY-NC or CC-BY-ND license",
            "description": 'To comply with Horizon Europe\'s open science requirements, monographs or other long-text must be available under the latest Creative Commons Attribution International license (CC-BY) or a license with equivalent rights. Monographs and other long-texts may exclude commercial or derivative works (i.e. CC-BY-NC or CC-BY-ND). <a href="/communities/eu/pages/open-science" target="_blank">Learn more</a>',
            "level": "info",
            "condition": {
                "type": "logical",
                "operator": "and",
                "expressions": [
                    {
                        "type": "comparison",
                        "left": {"type": "field", "path": "metadata.resource_type.id"},
                        "operator": "in",
                        "right": ["publication-book", "publication-section"],
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
                            "cc-by-1.0",
                            "cc-by-2.0",
                            "cc-by-2.5",
                            "cc-by-3.0",
                            "cc-by-3.0-at",
                            "cc-by-3.0-us",
                            "cc-by-4.0",
                            "cc-by-nc-1.0",
                            "cc-by-nc-2.0",
                            "cc-by-nc-2.5",
                            "cc-by-nc-3.0",
                            "cc-by-nc-4.0",
                            "cc-by-nc-nd-1.0",
                            "cc-by-nc-nd-2.0",
                            "cc-by-nc-nd-2.5",
                            "cc-by-nc-nd-3.0",
                            "cc-by-nc-nd-3.0-igo",
                            "cc-by-nc-nd-4.0",
                            "cc-by-nd-1.0",
                            "cc-by-nd-2.0",
                            "cc-by-nd-2.5",
                            "cc-by-nd-3.0",
                            "cc-by-nd-4.0",
                        ],
                    },
                }
            ],
        },
        {
            "id": "license:osi/software",
            "title": "Software License",
            "message": "Software should have an OSI-approved license",
            "description": 'To comply with Horizon Europe\'s open science requirements, software should be available under a OSI-approved license (following the principle as open as possible, as closed as necessary and with exceptions possible). <a href="/communities/eu/pages/open-science" target="_blank">Learn more</a>',
            "level": "info",
            "condition": {
                "type": "logical",
                "operator": "and",
                "expressions": [
                    {
                        "type": "comparison",
                        "left": {"type": "field", "path": "metadata.resource_type.id"},
                        "operator": "==",
                        "right": "software",
                    },
                    {
                        "type": "comparison",
                        "left": {"type": "field", "path": "access.files"},
                        "operator": "==",
                        "right": "public",
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
                            "0bsd",
                            "aal",
                            "afl-1.1",
                            "afl-1.2",
                            "afl-2.0",
                            "afl-2.1",
                            "afl-3.0",
                            "agpl-3.0-only",
                            "agpl-3.0-or-later",
                            "apache-1.1",
                            "apache-2.0",
                            "apl-1.0",
                            "apsl-1.0",
                            "apsl-1.1",
                            "apsl-1.2",
                            "apsl-2.0",
                            "artistic-1.0",
                            "artistic-1.0-cl8",
                            "artistic-1.0-perl",
                            "artistic-2.0",
                            "bsd-1-clause",
                            "bsd-2-clause",
                            "bsd-2-clause-patent",
                            "bsd-3-clause",
                            "bsd-3-clause-lbnl",
                            "bsl-1.0",
                            "cal-1.0",
                            "cal-1.0-combined-work-exception",
                            "catosl-1.1",
                            "cddl-1.0",
                            "cecill-2.1",
                            "cnri-python",
                            "cpal-1.0",
                            "cpl-1.0",
                            "cua-opl-1.0",
                            "ecl-1.0",
                            "ecl-2.0",
                            "efl-1.0",
                            "efl-2.0",
                            "entessa",
                            "epl-1.0",
                            "epl-2.0",
                            "eudatagrid",
                            "eupl-1.1",
                            "eupl-1.2",
                            "fair",
                            "frameworx-1.0",
                            "gpl-2.0-only",
                            "gpl-2.0-or-later",
                            "gpl-3.0-only",
                            "gpl-3.0-or-later",
                            "hpnd",
                            "intel",
                            "ipa",
                            "ipl-1.0",
                            "isc",
                            "lgpl-2.0-only",
                            "lgpl-2.0-or-later",
                            "lgpl-2.1-only",
                            "lgpl-2.1-or-later",
                            "lgpl-3.0-only",
                            "lgpl-3.0-or-later",
                            "liliq-p-1.1",
                            "liliq-r-1.1",
                            "liliq-rplus-1.1",
                            "lpl-1.0",
                            "lpl-1.02",
                            "lppl-1.3c",
                            "miros",
                            "mit",
                            "mit-0",
                            "motosoto",
                            "mpl-1.0",
                            "mpl-1.1",
                            "mpl-2.0",
                            "mpl-2.0-no-copyleft-exception",
                            "ms-pl",
                            "ms-rl",
                            "mulanpsl-2.0",
                            "multics",
                            "nasa-1.3",
                            "naumen",
                            "ncsa",
                            "ngpl",
                            "nokia",
                            "nposl-3.0",
                            "ntp",
                            "oclc-2.0",
                            "ofl-1.1",
                            "ofl-1.1-no-rfn",
                            "ofl-1.1-rfn",
                            "ogtsl",
                            "oldap-2.8",
                            "oset-pl-2.1",
                            "osl-1.0",
                            "osl-2.0",
                            "osl-2.1",
                            "osl-3.0",
                            "php-3.0",
                            "php-3.01",
                            "postgresql",
                            "python-2.0",
                            "qpl-1.0",
                            "rpl-1.1",
                            "rpl-1.5",
                            "rpsl-1.0",
                            "rscpl",
                            "simpl-2.0",
                            "sissl",
                            "sleepycat",
                            "spl-1.0",
                            "ucl-1.0",
                            "unicode-dfs-2016",
                            "unlicense",
                            "upl-1.0",
                            "vsl-1.0",
                            "w3c",
                            "watcom-1.0",
                            "xnet",
                            "zlib",
                            "zpl-2.0",
                        ],
                    },
                }
            ],
        },
        {
            "id": "license:cc-by-0/other",
            "title": "Records should be CC-BY or CC-0 License",
            "message": "Submissions (except journal articles, books, or software) should have CC BY license, CC0 dedication or equivalent",
            "description": 'To comply with Horizon Europe\'s open science requirements, all submission except journal articles, books and software must be available under the latest available Creative Commons Attribution International license (CC-BY), or Creative Commons Public Domain Dedication (CC0) or a license/dedication with equivalent rights (following the principle as open as possible, as closed as necessary and with exceptions possible). <a href="/communities/eu/pages/open-science" target="_blank">Learn more</a>',
            "level": "info",
            "condition": {
                "type": "logical",
                "operator": "and",
                "expressions": [
                    {
                        "type": "comparison",
                        "left": {"type": "field", "path": "metadata.resource_type.id"},
                        "operator": "not in",
                        "right": [
                            "publication-article",
                            "publication-book",
                            "publication-section",
                            "software",
                        ],
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
                            "cc0-1.0",
                            "cc-by-1.0",
                            "cc-by-2.0",
                            "cc-by-2.5",
                            "cc-by-3.0",
                            "cc-by-3.0-at",
                            "cc-by-3.0-us",
                            "cc-by-4.0",
                        ],
                    },
                }
            ],
        },
        {
            "id": "creators:identifier",
            "title": "Creator Identifiers",
            "message": "All creators should have a persistent identifier (e.g. an ORCID)",
            "description": 'To comply with Horizon Europe\'s open science requirements, you should provide persistent identifiers for creators (e.g., ORCID, GND, or ISNI). <a href="/communities/eu/pages/open-science" target="_blank">Learn more</a>',
            "level": "info",
            "condition": {
                "type": "list",
                "operator": "exists",
                "path": "metadata.creators",
                "predicate": {},
            },
            "checks": [
                {
                    "type": "list",
                    "operator": "all",
                    "path": "metadata.creators",
                    "predicate": {
                        "type": "logical",
                        "operator": "and",
                        "expressions": [
                            {"type": "field", "path": "person_or_org.identifiers"},
                            {
                                "type": "list",
                                "operator": "any",
                                "path": "person_or_org.identifiers",
                                "predicate": {"type": "field", "path": "identifier"},
                            },
                        ],
                    },
                }
            ],
        },
        {
            "id": "contributors:identifier",
            "title": "Contributor Identifiers",
            "message": "All contributors should have a persistent identifier (e.g. an ORCID)",
            "description": 'To comply with Horizon Europe\'s open science requirements, you should provide persistent identifiers for contributors (e.g., ORCID, GND, or ISNI). <a href="/communities/eu/pages/open-science" target="_blank">Learn more</a>',
            "level": "info",
            "condition": {
                "type": "list",
                "operator": "exists",
                "path": "metadata.contributors",
                "predicate": {},
            },
            "checks": [
                {
                    "type": "list",
                    "operator": "all",
                    "path": "metadata.contributors",
                    "predicate": {
                        "type": "logical",
                        "operator": "and",
                        "expressions": [
                            {"type": "field", "path": "person_or_org.identifiers"},
                            {
                                "type": "list",
                                "operator": "any",
                                "path": "person_or_org.identifiers",
                                "predicate": {"type": "field", "path": "identifier"},
                            },
                        ],
                    },
                }
            ],
        },
        {
            "id": "funding:eu",
            "title": "EU Funding",
            "message": "Submissions must have a grant/award from the European Commission",
            "description": 'The EU Open Research Repository only accepts submissions stemming from one of EU’s research and innovation funding programmes, which currently include Horizon Europe (including ERC, MSCA), earlier Framework Programmes (eg Horizon 2020), as well as Euratom. Please ensure you add a standard or custom grant/award stemming from the European Commission. <a href="/communities/eu/pages/open-science" target="_blank">Learn more</a>',
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
                        "right": "00k4n6c32",
                    },
                }
            ],
        },
    ]
}

SUB_COMMUNITY_RULES = {
    "rules": [
        {
            "id": "funding:project",
            "title": "Project Funding",
            "message": "Submissions must have the __AWARD_ACRONYM__ (__AWARD_NUMBER__) grant/award",
            "description": 'You are submitting to an EU project community for __AWARD_ACRONYM__ (__AWARD_NUMBER__) and you must therefore add the grant/award. <a href="/communities/eu/pages/open-science" target="_blank">Learn more</a>',
            "level": "error",
            "checks": [
                {
                    "type": "list",
                    "operator": "any",
                    "path": "metadata.funding",
                    "predicate": {
                        "type": "comparison",
                        "left": {"type": "field", "path": "award.id"},
                        "operator": "==",
                        "right": None,
                    },
                }
            ],
        },
    ]
}

FILE_FORMAT_CONFIG = {
    # TODO: Link needs to be updated
    "closed_format_description": "Using closed or proprietary formats hinders reusability and preservation of published files. <a href='https://support.zenodo.org/help/en-gb/28' target='_blank' >Learn more</a>",
}


def create_eu_checks():
    eu_comm = community_service.record_cls.pid.resolve("eu")
    create_metadata_checks(eu_comm)
    create_file_format_checks(eu_comm)
    print("EU Open Research Repository community checks created/updated successfully.")

    # Create checks for sub-communities
    sub_communities = community_service._search(
        "search",
        system_identity,
        params={},
        extra_filter=dsl.query.Bool(
            "must", must=[dsl.Q("term", **{"parent.id": str(eu_comm.id)})]
        ),
        permission_action="read",
        search_preference=None,
    ).scan()

    for sub_community in sub_communities:
        sub_community = sub_community.to_dict()
        sub_id = sub_community["id"]
        funding = sub_community.get("metadata", {}).get("funding", [])
        if len(funding) != 1:
            print(
                f"Skipping {sub_id} as it does not have exactly one funding: {funding}"
            )
            continue

        check_config_params = deepcopy(SUB_COMMUNITY_RULES)
        # Update the award ID in the params
        if "id" not in funding[0]["award"]:
            print(f"Skipping {sub_id} as it does not have a funding ID: {funding}")
            continue

        check_config_params["rules"][0]["checks"][0]["predicate"]["right"] = funding[0][
            "award"
        ]["id"]

        # Update the award acronym and number in the message and description
        award_acronym = funding[0]["award"]["acronym"]
        award_number = funding[0]["award"]["number"]

        check_message = check_config_params["rules"][0]["message"]
        check_message = check_message.replace("__AWARD_ACRONYM__", award_acronym)
        check_message = check_message.replace("__AWARD_NUMBER__", award_number)
        check_config_params["rules"][0]["message"] = check_message

        check_description = check_config_params["rules"][0]["description"]
        check_description = check_description.replace(
            "__AWARD_ACRONYM__", award_acronym
        )
        check_description = check_description.replace("__AWARD_NUMBER__", award_number)
        check_config_params["rules"][0]["description"] = check_description

        existing_check = CheckConfig.query.filter_by(
            community_id=sub_community["id"], check_id="metadata"
        ).one_or_none()
        if existing_check:
            existing_check.params = check_config_params
        else:
            check_config = CheckConfig(
                community_id=sub_community["id"],
                check_id="metadata",
                params=check_config_params,
                severity=Severity.INFO,
                enabled=True,
            )
            db.session.add(check_config)
        db.session.commit()
    print("EU subcommunity checks created/updated successfully.")


def create_metadata_checks(eu_comm):
    existing_check = CheckConfig.query.filter_by(
        community_id=eu_comm.id, check_id="metadata"
    ).one_or_none()
    if existing_check:  # If it exists, update it
        existing_check.params = EU_RULES
    else:  # ...create it
        check_config = CheckConfig(
            community_id=eu_comm.id,
            check_id="metadata",
            params=EU_RULES,
            severity=Severity.INFO,
            enabled=True,
        )
        db.session.add(check_config)
    db.session.commit()
    print(f"Metadata checks created/updated successfully for community {eu_comm.slug}.")


def create_file_format_checks(eu_comm):
    existing_check = CheckConfig.query.filter_by(
        community_id=eu_comm.id, check_id="file_formats"
    ).one_or_none()
    if existing_check:  # If it exists, update it
        existing_check.params = FILE_FORMAT_CONFIG
    else:  # ...create it
        check_config = CheckConfig(
            community_id=eu_comm.id,
            check_id="file_formats",
            params=FILE_FORMAT_CONFIG,
            severity=Severity.INFO,
            enabled=True,
        )
        db.session.add(check_config)
    db.session.commit()
    print(
        f"File format checks created/updated successfully for community {eu_comm.slug}."
    )


if __name__ == "__main__":
    create_eu_checks()
