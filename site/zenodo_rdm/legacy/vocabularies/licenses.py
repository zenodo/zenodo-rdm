# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Zenodo-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Licenses vocabularies for legacy compatibility."""

import importlib.resources as pkg_resources
import json

from zenodo_rdm.legacy.vocabularies import data


def _load_json(filename):
    with pkg_resources.open_text(data, filename) as raw_data:
        loaded = json.load(raw_data)
    return loaded


LEGACY_LICENSES = {l["id"]: l for l in _load_json("legacy_licenses.json")}

# Licenses mapping (Legacy -> RDM)
LEGACY_TO_RDM_MAP = _load_json("legacy_to_rdm_map.json")

# Inverse mapping (RDM->Legacy)
RDM_TO_LEGACY_MAP = {v: k for k, v in LEGACY_TO_RDM_MAP.items()}

LEGACY_ALIASES = {
    "BSD-3-Clause": "bsd-3-clause",
    "BSD-2-Clause": "bsd-2-clause",
    "AFL-3.0": "afl-3.0",
    "APL-1.0": "apl1.0",
    "AGPL-3.0": "agpl-v3",
    "Against-DRM": "against-drm",
    "Apache-2.0": "apache2.0",
    "Apache-2.0": "apache",
    "APSL-2.0": "apsl-2.0",
    "Artistic-2.0": "artistic-license-2.0",
    "AAL": "attribution",
    "BSL-1.0": "bsl1.0",
    "CUA-OPL-1.0": "cuaoffice",
    "CDDL-1.0": "cddl1",
    "CPAL-1.0": "cpal_1.0",
    "CATOSL-1.1": "ca-tosl1.1",
    "CC-BY-SA-4.0": "cc-by-sa",
    "CC-BY-4.0": "cc-by",
    "CC0-1.0": "cc-zero",
    "DSL": "dsl",
    "EUDatagrid": "eudatagrid",
    "EPL-1.0": "eclipse-1.0",
    "ECL-2.0": "ecl2",
    "EFL-2.0": "ver2_eiffel",
    "EFL-2.0": "eiffel",
    "Entessa": "entessa",
    "EUPL-1.1": "eupl-1.1",
    "Fair": "fair",
    "Frameworx-1.0": "frameworx",
    "FAL-1.3": "fal",
    "GFDL-1.3-no-cover-texts-no-invariant-sections": "gfdl",
    "GPL-2.0": "gpl-2.0",
    "GPL-3.0": "gpl-3.0",
    "LGPL-2.1": "lgpl-2.1",
    "LGPL-3.0": "lgpl-3.0",
    "geogratis": "geogratis",
    "hesa-withrights": "hesa-withrights",
    "IPL-1.0": "ibmpl",
    "IPA": "ipafont",
    "ISC": "isc-license",
    "Intel": "intel-osl",
    "notspecified": "notspecified",
    "localauth-withrights": "localauth-withrights",
    "LPL-1.02": "lucent1.02",
    "MIT": "mit-license",
    "mitre": "mitre",
    "met-office-cp": "met-office-cp",
    "MS-PL": "ms-pl",
    "MS-RL": "ms-rl",
    "MirOS": "miros",
    "Motosoto": "motosoto",
    "MPL-1.0": "mozilla",
    "MPL-1.1": "mozilla1.1",
    "Multics": "multics",
    "NASA-1.3": "nasa1.3",
    "NTP": "ntp-license",
    "Naumen": "naumen",
    "NGPL": "nethack",
    "Nokia": "nokia",
    "NPOSL-3.0": "nosl3.0",
    "OCLC-2.0": "oclc2",
    "ODC-BY-1.0": "odc-by",
    "ODbL-1.0": "odc-odbl",
    "ODC-PDDL-1.0": "odc-pddl",
    "OFL-1.1": "openfont",
    "OGTSL": "opengroup",
    "OSL-3.0": "osl-3.0",
    "other-at": "other-at",
    "other-nc": "other-nc",
    "other-closed": "other-closed",
    "other-open": "other-open",
    "other-pd": "other-pd",
    "PHP-3.0": "php",
    "Python-2.0": "pythonsoftfoundation",
    "CNRI-Python": "pythonpl",
    "QPL-1.0": "qtpl",
    "RPSL-1.0": "real",
    "RPL-1.5": "rpl1.5",
    "RSCPL": "ricohpl",
    "SimPL-2.0": "simpl-2.0",
    "Sleepycat": "sleepycat",
    "dli-model-use": "dli-model-use",
    "SISSL": "sun-issl",
    "SPL-1.0": "sunpublic",
    "Watcom-1.0": "sybase",
    "Talis": "tcl",
    "PostgreSQL": "postgresql",
    "ukclickusepsi": "ukclickusepsi",
    "ukcrown-withrights": "ukcrown-withrights",
    "ukcrown": "ukcrown",
    "OGL-UK-1.0": "uk-ogl",
    "ukpsi": "ukpsi",
    "NCSA": "uoi-ncsa",
    "VSL-1.0": "vovidapl",
    "W3C": "w3c",
    "Xnet": "xnet",
    "ZPL-2.0": "zpl",
    "WXwindows": "wxwindows",
    "Zlib": "zlib-license",
    "CC-BY-NC-4.0": "cc-by-nc-4.0",
}


def legacy_to_rdm(license):
    """Returns an RDM license given a zenodo legacy license."""
    _license = LEGACY_ALIASES.get(license, license)

    return LEGACY_TO_RDM_MAP.get(_license)


def rdm_to_legacy(right):
    """Returns a zenodo legacy license given an RDM license."""
    # Aliasing is not needed on legacy zenodo, the license's id is enough.
    return RDM_TO_LEGACY_MAP.get(right)
