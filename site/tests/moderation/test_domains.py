# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Domain moderation tests."""

import pytest

from zenodo_rdm.moderation.models import LinkDomain, LinkDomainStatus


@pytest.fixture
def domains(db):
    """Create test domains."""
    domains = [
        LinkDomain.create("blog.io", LinkDomainStatus.SAFE),
        LinkDomain.create("spam.blog.io", LinkDomainStatus.BANNED),
        LinkDomain.create("edu.ch", LinkDomainStatus.SAFE),
        LinkDomain.create("cam", LinkDomainStatus.BANNED),
    ]
    db.session.commit()
    return domains


@pytest.mark.parametrize(
    "domain,expected_status",
    [
        ("http://example.com/content", None),
        ("https://blog.io/article", LinkDomainStatus.SAFE),
        ("https://spam.blog.io/article", LinkDomainStatus.BANNED),
        ("http://other.blog.io/article", LinkDomainStatus.SAFE),
        ("https://physics.edu.ch/article", LinkDomainStatus.SAFE),
        ("https://math.edu.ch/article", LinkDomainStatus.SAFE),
        ("http://spam.cam/content", LinkDomainStatus.BANNED),
        ("http://sub.spam.cam/content", LinkDomainStatus.BANNED),
    ],
)
def test_lookup_domain(domains, domain, expected_status):
    """Test domain lookup."""
    if expected_status is None:
        assert LinkDomain.lookup_domain(domain) is None
    else:
        assert LinkDomain.lookup_domain(domain).status == expected_status
