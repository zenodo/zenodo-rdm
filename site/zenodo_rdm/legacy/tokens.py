# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Zenodo is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Legacy token serializers.

Ported from <https://github.com/zenodo/zenodo-accessrequests/blob/master/zenodo_accessrequests/tokens.py>.
"""

from collections import namedtuple
from datetime import datetime
from functools import partial

from flask import current_app, flash, request, session
from invenio_i18n import _
from itsdangerous import BadData, SignatureExpired
from itsdangerous.jws import JSONWebSignatureSerializer, TimedJSONWebSignatureSerializer

_Need = namedtuple("Need", ["method", "value"])
LegacySecretLinkNeed = partial(_Need, "legacy_secret_link")


SUPPORTED_DIGEST_ALGORITHMS = ("HS256", "HS512")


class TokenMixin:
    """Mix-in class for token serializers."""

    def validate_token(self, token, expected_data=None):
        """Validate secret link token.

        :param token: Token value.
        :param expected_data: A dictionary of key/values that must be present
            in the data part of the token.
        """
        try:
            # Load token and remove random data.
            data = self.load_token(token)

            # Compare expected data with data in token.
            if expected_data:
                for k in expected_data:
                    if expected_data[k] != data["data"].get(k):
                        return None
            return data
        except BadData:
            return None

    def load_token(self, token, force=False):
        """Load data in a token.

        :param token: Token to load.
        :param force: Load token data even if signature expired.
                      Default: False.
        """
        try:
            data = self.loads(token)
        except SignatureExpired as e:
            if not force:
                raise
            data = e.payload

        del data["rnd"]
        return data


class SecretLinkSerializer(JSONWebSignatureSerializer, TokenMixin):
    """Serializer for secret links."""

    def __init__(self, **kwargs):
        """Initialize underlying JSONWebSignatureSerializer."""
        super(SecretLinkSerializer, self).__init__(
            current_app.config["SECRET_KEY"], salt="accessrequests-link", **kwargs
        )


class TimedSecretLinkSerializer(TimedJSONWebSignatureSerializer, TokenMixin):
    """Serializer for expiring secret links."""

    def __init__(self, expires_at=None, **kwargs):
        """Initialize underlying TimedJSONWebSignatureSerializer."""
        assert isinstance(expires_at, datetime) or expires_at is None

        dt = expires_at - datetime.now() if expires_at else None

        super(TimedSecretLinkSerializer, self).__init__(
            current_app.config["SECRET_KEY"],
            expires_in=int(dt.total_seconds()) if dt else None,
            salt="accessrequests-timedlink",
            **kwargs,
        )


class SecretLinkFactory:
    """Functions for validating any secret link tokens."""

    @classmethod
    def validate_token(cls, token, expected_data=None):
        """Validate a secret link token (non-expiring + expiring)."""
        for algorithm in SUPPORTED_DIGEST_ALGORITHMS:
            s = SecretLinkSerializer(algorithm_name=algorithm)
            st = TimedSecretLinkSerializer(algorithm_name=algorithm)

            try:
                for serializer in (s, st):
                    data = serializer.validate_token(token, expected_data=expected_data)
                    if data:
                        return data
            except SignatureExpired:  # move to next algorithm
                raise
            except BadData:
                continue  # move to next serializer/algorithm

    @classmethod
    def load_token(cls, token, force=False):
        """Validate a secret link token (non-expiring + expiring)."""
        for algorithm in SUPPORTED_DIGEST_ALGORITHMS:
            s = SecretLinkSerializer(algorithm_name=algorithm)
            st = TimedSecretLinkSerializer(algorithm_name=algorithm)
            for serializer in (s, st):
                try:
                    data = serializer.load_token(token, force=force)
                    if data:
                        return data
                except SignatureExpired:
                    raise  # Signature was parsed and is expired
                except BadData:
                    continue  # move to next serializer/algorithm


def verify_legacy_secret_link(identity):
    """Verify the legacy secret linlk token."""
    token = None
    token_source = None
    arg_key = "token"
    session_key = "_legacy_secret_link_token"
    arg_token = request.args.get(arg_key, None)
    session_token = session.get(session_key, None)
    if arg_token:
        token = arg_token
        token_source = "arg"
    elif session_token:
        token = session_token
        token_source = "session"

    if token:
        try:
            data = SecretLinkFactory.load_token(token)
            if data:
                identity.provides.add(LegacySecretLinkNeed(str(data["data"]["recid"])))
                session[session_key] = token
        except SignatureExpired:
            if token_source == "arg":
                flash(_("Your shared link has expired."))
            session.pop(session_key, None)
