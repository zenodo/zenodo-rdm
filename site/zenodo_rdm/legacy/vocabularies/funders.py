# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Zenodo-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Funders vocabularies for legacy compatibility."""

# based on
# DOI to id https://digital-repositories.web.cern.ch/zenodo/support/operations/#openaire-grants-import
# id to ROR: https://github.com/inveniosoftware/invenio-vocabularies/blob/master/invenio_vocabularies/config.py#L64
FUNDER_DOI_TO_ROR = {
    "10.13039/501100001665": "00rbzpz17",
    "10.13039/501100002341": "05k73zm37",
    "10.13039/501100000923": "05mmh0f86",
    "10.13039/100018231": "03zj4c476",
    "10.13039/501100000024": "01gavpb45",
    "10.13039/501100000780": "00k4n6c32",
    "10.13039/501100000806": "02k4b9v70",
    "10.13039/501100001871": "00snfqn58",
    "10.13039/501100002428": "013tf3c58",
    "10.13039/501100004488": "03n51vw80",
    "10.13039/501100004564": "01znas443",
    "10.13039/501100000925": "011kf5r70",
    "10.13039/100000002": "01cwqze88",
    "10.13039/501100000038": "01h531d29",
    "10.13039/100000001": "021nxhr62",
    "10.13039/501100003246": "04jsz6e67",
    # NOTE: RCUK was succeeded by UKRI. All awards/grants were transferred, so
    #       we're also remapping the funder IDs to point to UKRI (001aqnf71)
    "10.13039/501100000690": "001aqnf71",
    "10.13039/100014013": "001aqnf71",
    "10.13039/501100001602": "0271asj38",
    "10.13039/501100001711": "00yjd3n13",
    "10.13039/100001345": "006cvnv84",
    "10.13039/501100004410": "04w9kkr77",
    "10.13039/100004440": "029chgv08",
    "10.13039/501100006364": "03m8vkq32",
}

FUNDER_ROR_TO_DOI = {v: k for k, v in FUNDER_DOI_TO_ROR.items()}
