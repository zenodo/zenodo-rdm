# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Zenodo-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Licenses vocabularies for legacy compatibility."""

from zenodo_rdm.legacy.vocabularies.utils import _load_json

LEGACY_LICENSES = {l["id"]: l for l in _load_json("legacy_licenses.json")}

# Licenses mapping (Legacy -> RDM)
LEGACY_TO_RDM_MAP = _load_json("legacy_to_rdm_map.json")

# Inverse mapping (RDM->Legacy)
RDM_TO_LEGACY_MAP = {v: k for k, v in LEGACY_TO_RDM_MAP.items()}

LEGACY_ALIASES = {
    "agpl-v3": "agpl-3.0-only",
    "agpl-3.0": "agpl-3.0-only",
    "apache": "apache-2.0",
    "apache2.0": "apache-2.0",
    "apl1.0": "apl-1.0",
    "artistic-license-2.0": "Artistic-2.0",
    "attribution": "AAL",
    "bsl1.0": "BSL-1.0",
    "ca-tosl1.1": "CATOSL-1.1",
    "cc-by": "CC-BY-4.0",
    "cc-by-sa": "CC-BY-SA-4.0",
    "cc-zero": "CC0-1.0",
    "cddl1": "CDDL-1.0",
    "cpal_1.0": "CPAL-1.0",
    "cuaoffice": "CUA-OPL-1.0",
    "ecl2": "ECL-2.0",
    "eclipse-1.0": "EPL-1.0",
    "eiffel": "EFL-2.0",
    "fal": "FAL-1.3",
    "frameworx": "Frameworx-1.0",
    "gfdl": "GFDL-1.3-no-cover-texts-no-invariant-sections",
    "ibmpl": "IPL-1.0",
    "intel-osl": "Intel",
    "ipafont": "IPA",
    "isc-license": "ISC",
    "lucent1.02": "LPL-1.02",
    "mit-license": "MIT",
    "mozilla": "MPL-1.0",
    "mozilla1.1": "MPL-1.1",
    "nasa1.3": "NASA-1.3",
    "nethack": "NGPL",
    "nosl3.0": "NPOSL-3.0",
    "ntp-license": "NTP",
    "oclc2": "OCLC-2.0",
    "odc-by": "ODC-BY-1.0",
    "odc-odbl": "ODbL-1.0",
    "odc-pddl-1.0": "pddl-1.0",
    "openfont": "OFL-1.1",
    "opengroup": "OGTSL",
    "php": "PHP-3.0",
    "pythonpl": "CNRI-Python",
    "pythonsoftfoundation": "Python-2.0",
    "qtpl": "QPL-1.0",
    "real": "RPSL-1.0",
    "ricohpl": "RSCPL",
    "rpl1.5": "RPL-1.5",
    "sun-issl": "SISSL",
    "sunpublic": "SPL-1.0",
    "sybase": "Watcom-1.0",
    "tcl": "tcl",
    "uk-ogl": "OGL-UK-1.0",
    "uoi-ncsa": "NCSA",
    "ver2_eiffel": "EFL-2.0",
    "vovidapl": "VSL-1.0",
    "zlib-license": "Zlib",
    "zpl": "ZPL-2.0",
}


def legacy_to_rdm(license):
    """Returns an RDM license given a zenodo legacy license."""
    if not license:
        return
    normalized = license.lower().strip()
    _license = LEGACY_ALIASES.get(normalized, normalized).lower()

    return LEGACY_TO_RDM_MAP.get(_license)


def rdm_to_legacy(right):
    """Returns a zenodo legacy license given an RDM license."""
    # Aliasing is not needed on legacy zenodo, the license's id is enough.
    return RDM_TO_LEGACY_MAP.get(right)
