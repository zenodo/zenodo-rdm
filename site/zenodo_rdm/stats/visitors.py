# SPDX-FileCopyrightText: 2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Visitor classifier for usage-statistics filtering.

Composes the counter-robots COUNTER baseline and extended preset with Zenodo's
instance-specific lists, and wires it to invenio-stats via
``STATS_VISITOR_CLASSIFIER``.
"""

from importlib.resources import files

from counter_robots import (
    ClassifierBuilder,
    asns_from,
    counter_preset,
    extended_preset,
    maxminddb_resolver,
    patterns_from,
)


def _data(filename):
    """Read a packaged instance data file."""
    return (files("zenodo_rdm.stats") / "data" / filename).read_text()


def zenodo_preset(builder):
    """Add Zenodo instance-specific robots, machines and datacenter ASNs.

    These are the long tail of one-off scrapers and the genuine hosting networks
    that the generic counter-robots lists do not cover. User-agent patterns are
    matched case-insensitively.
    """
    builder.robots(patterns_from(_data("robots.txt")), ignore_case=True)
    builder.machines(patterns_from(_data("machines.txt")), ignore_case=True)
    builder.datacenter_asns(asns_from(_data("datacenter_asns.txt")))


def visitor_classifier(app):
    """Build the Zenodo visitor classifier.

    The COUNTER baseline plus the extended preset plus Zenodo's instance lists,
    with datacenter IP resolution when ``STATS_VISITOR_ASN_DB`` points at a
    GeoLite2-ASN database (needs the ``counter-robots[asn]`` extra).
    """
    builder = (
        ClassifierBuilder().use(counter_preset).use(extended_preset).use(zenodo_preset)
    )
    asn_db = app.config.get("STATS_VISITOR_ASN_DB")
    if asn_db:
        builder.asn_resolver(maxminddb_resolver(asn_db))
    return builder.build()
