# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Zenodo-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""OpenAIRE tests."""


from zenodo_rdm.openaire.proxies import current_openaire


def test_openaire_type(app):
    """Test OpenAIRE type."""

    state = current_openaire.state
    assert set(state.inverse_openaire_community_map.keys()) == set(["c1", "c2", "c3"])

    assert set(state.inverse_openaire_community_map["c1"]) == set(["foo", "bar"])
    assert set(state.inverse_openaire_community_map["c2"]) == set(["foo"])
    assert set(state.inverse_openaire_community_map["c3"]) == set(["bar"])

    assert set(state.openaire_communities.keys()) == set(["foo", "bar"])
