# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo migrator actions transform."""


from invenio_rdm_migrator.transform import BaseTxTransform

from ..actions.transform import (
    DraftCreateAction,
    UserDeactivationAction,
    UserEditAction,
    UserRegistrationAction,
)


class ZenodoTxTransform(BaseTxTransform):
    """Zenodo transaction transform."""

    actions = [
        DraftCreateAction,
        UserDeactivationAction,
        UserEditAction,
        UserRegistrationAction,
    ]
