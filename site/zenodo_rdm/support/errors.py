# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""ZenodoRDM support error classes."""

from ..errors import ZenodoRDMError


class ConfirmationEmailNotSent(ZenodoRDMError):
    """Implements an error when a support confirmation e-mail was not sent."""

    def __init__(self, message):
        """Initialise error."""
        super().__init__("Confirmation email failed to send. Error: {}".format(message))


class SupportEmailNotSent(ZenodoRDMError):
    """Implements an error when a support e-mail was not sent."""

    def __init__(self, message):
        """Initialise error."""
        super().__init__("Support email failed to send. Error: {}".format(message))
