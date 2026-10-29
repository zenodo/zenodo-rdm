# SPDX-FileCopyrightText: 2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later

"""Model Context Protocol server for the Zenodo REST API."""

from .server import create_server

__version__ = "0.1.0"

__all__ = ("create_server", "__version__")
