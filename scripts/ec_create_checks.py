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


def create_eu_checks():
    eu_comm = community_service.record_cls.pid.resolve("eu")
    # Check if there is already a check for the community
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
    print("EU checks created/updated successfully.")

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
        check_config_params["rules"][0]["checks"][0]["predicate"]["right"] = funding[0][
            "award"
        ]["id"]

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
    print("EU checks created/updated successfully.")


if __name__ == "__main__":
    create_eu_checks()


EU_RULES = {
    "rules": [
        {
            "id": "access:open/publication",
            "title": "Open Access Publication",
            "message": "Publication articles must be Open Access",
            "description": "The EU curation policy requires publication articles must be Open Access",
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
                    "left": {"type": "field", "path": "access.files"},
                    "operator": "==",
                    "right": "public",
                }
            ],
        },
        {
            "id": "journal:title/publication",
            "title": "Journal Information",
            "message": "Publication articles must state the journal it was published in",
            "description": "The EU curation policy requires publication articles must state the journal it was published in",
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
            "message": "All records must have a license",
            "description": "The EU curation policy requires all records to have a license",
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
            "message": "Journal article should have a CC-BY license",
            "description": "The EU curation policy recommends journal articles to have a CC-BY license",
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
            "message": "Book  should have a CC BY, NC or SA license",
            "description": "The EU curation policy recommends books to have a CC BY, NC or SA license",
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
            "message": "Software must have an appropriate license",
            "description": "The EU curation policy requires software to have an appropriate license",
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
            "message": "Unless the record is a article, book, section or software, it should be CC BY or CC 0",
            "description": "The EU curation policy suggests records should have a CC BY or CC 0 license",
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
            "message": "All creators must have at least one identifier",
            "description": "The EU curation policy suggests all creators should have at least one identifier",
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
            "message": "All contributors must have at least one identifier",
            "description": "The EU curation policy suggests all contributors should have at least one identifier",
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
            "message": "Records must have at least one EU-funded project",
            "description": "The EU curation policy requires that funding from the EC is always specified",
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
            "message": "Records must specify the project's funding",
            "description": "The EU curation policy requires that funding from the EC is always specified for projects",
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
