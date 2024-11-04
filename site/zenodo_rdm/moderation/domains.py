# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Rules for moderation."""

import re


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

    @staticmethod
    def extract_domain(url):
        """Extract and reverse domain parts from a given URL."""
        pattern = r"^(?:https?://)?(?:www\.)?([^/]+)"
        match = re.search(pattern, url)
        if match:
            domain = match.group(1)
            domain_parts = domain.split(".")
            return domain_parts[::-1]
        return None

    def get_status(self, url):
        """Retrieve the status of a URL's domain."""
        domain_parts = self.extract_domain(url)
        current = self.tree
        for part in domain_parts:
            if part in current:
                current = current[part]
                if "status" in current:
                    return current["status"]
            else:
                break
        return None
