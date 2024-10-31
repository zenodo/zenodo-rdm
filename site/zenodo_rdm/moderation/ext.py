# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""ZenodoRDM Moderation module."""

from flask import current_app
from werkzeug.utils import cached_property


class ZenodoModeration:
    """Zenodo content moderation extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        app.extensions["zenodo-moderation"] = self

    @cached_property
    def domain_tree(self):
        """Initialize and return the DomainTree instance with config-based links."""
        domain_tree = DomainTree()
        domain_tree.initialize_links(
            current_app.config.get("CONTENT_MODERATION_BANNED_LINKS", []), "banned"
        )
        domain_tree.initialize_links(
            current_app.config.get("CONTENT_MODERATION_SAFE_LINKS", []), "safe"
        )
        return domain_tree


class DomainTree:
    """Domain tree structure to store and check status of domains."""

    def __init__(self):
        """Initialize an empty tree to hold domains and their statuses."""
        self.tree = {}

    def add_domain(self, domain, status):
        """Add a domain to the tree with its status: 'banned' or 'safe'."""
        parts = domain.strip(".").split(".")
        current = self.tree
        for part in parts:
            current = current.setdefault(part, {})
        current["status"] = status

    def initialize_links(self, links, status):
        """Helper method to add multiple links to the domain tree with a given status."""
        for domain in links:
            self.add_domain(domain, status)

    def get_status(self, domain_parts):
        """Retrieve the status of a domain."""
        current = self.tree
        for part in domain_parts:
            if part in current:
                current = current[part]
                if "status" in current:
                    return current["status"]
            else:
                break
        return None
