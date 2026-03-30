# SPDX-FileCopyrightText: 2023 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Zenodo migrator extract."""

from .kafka import KafkaExtract, KafkaExtractEnd

__all__ = (
    "KafkaExtract",
    "KafkaExtractEnd",
)
