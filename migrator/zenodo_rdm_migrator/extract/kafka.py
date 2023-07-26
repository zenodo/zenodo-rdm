# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Kafka extraction classes."""

from invenio_rdm_migrator.extract import Extract
from kafka import KafkaConsumer


class KafkaExtract(Extract):
    """Data extraction from Kafka.

    extract = KafkaExtract(
        topics=["zenodo-migration.public"],
        config={
            "bootstrap_servers": [
                "kafka01.server",
                "kafka02.server",
            ],
            "security_protocol": "SASL_SSL",
            "sasl_mechanism": "GSSAPI",
            "auto_offset_reset": "earliest",
        }
    )
    """

    def __init__(self, *, topics, config):
        """Constructor."""
        self.topics = topics
        self.config = config

    def run(self):
        """Yield one element at a time."""
        consumer = KafkaConsumer(*self.topics, **self.kafka_cfg)
        yield from consumer
