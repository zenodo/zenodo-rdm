# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Moderation models."""

import enum
from urllib.parse import urlparse

from invenio_db import db
from sqlalchemy_utils import ChoiceType, Timestamp


class LinkDomainStatus(enum.Enum):
    """Link domain status."""

    SAFE = "S"
    BANNED = "B"
    MODERATED = "M"


class LinkDomain(db.Model, Timestamp):
    """Link domain model."""

    __tablename__ = "link_domains"

    id = db.Column(db.Integer, primary_key=True)

    domain = db.Column(db.Text, nullable=False, unique=True)
    status = db.Column(
        ChoiceType(LinkDomainStatus, impl=db.CHAR(1)),
        nullable=False,
    )
    score = db.Column(db.Integer, nullable=True)
    reason = db.Column(db.Text, nullable=True)

    @classmethod
    def create(cls, domain, status, score=None, reason=None):
        """Create a link domain."""
        parts = domain.strip(".").split(".")
        domain = "." + ".".join(parts[::-1]).lower()
        ld = cls(domain=domain, status=status, score=score, reason=reason)
        db.session.add(ld)
        return ld

    @classmethod
    def lookup_domain(cls, url):
        """Lookup the status of a URL's domain."""
        try:
            parsed = urlparse(url)
        except ValueError:
            return None

        domain = parsed.netloc or ""
        domain = domain.lstrip("www.")
        domain_parts = domain.split(".")
        if not domain_parts:
            return None

        reversed_domain = "." + ".".join(domain_parts[::-1]).lower()
        return (
            cls.query.filter(
                # Exact match
                (LinkDomain.domain == reversed_domain)
                # Or subdomain match
                | db.literal(reversed_domain).like(LinkDomain.domain + ".%")
            )
            # Order by length of domain to get the most specific match
            .order_by(db.func.length(LinkDomain.domain).desc())
            .limit(1)
            .scalar()
        )


class ModerationQuery(db.Model):
    """Moderation queries model."""

    __tablename__ = "moderation_queries"

    id = db.Column(db.Integer, primary_key=True)
    """Primary key identifier for the moderation query."""

    score = db.Column(db.Integer, default=0)
    """Score associated with the query."""

    query_string = db.Column(db.Text, nullable=False)
    """Query string containing the filter criteria."""

    notes = db.Column(db.Text, nullable=True)
    """Additional notes or comments regarding the moderation query."""

    active = db.Column(db.Boolean, default=True)
    """Indicates whether the moderation query is currently active."""

    @classmethod
    def create(cls, query_string, notes=None, score=0, active=True):
        """Create a new moderation query with a configurable record class."""
        query = cls(query_string=query_string, notes=notes, score=score, active=active)
        db.session.add(query)

        return query

    @classmethod
    def get(cls, query_id=None):
        """Retrieve a moderation query by ID or return all queries if no ID is provided."""
        if query_id is not None:
            return cls.query.filter_by(id=query_id).one_or_none()

    def __repr__(self):
        """Get a string representation of the moderation query."""
        return f"<ModerationQuery id={self.id}, query_string={self.query_string}, score={self.score}, active={self.active}>"
