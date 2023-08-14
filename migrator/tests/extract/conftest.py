# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Migrator extract tests configuration."""

import gzip
from pathlib import Path
from types import SimpleNamespace

import jsonlines
import pytest
from kafka.consumer.fetcher import ConsumerRecord


@pytest.fixture(scope="session")
def kafka_data():
    """Yield Kafka ops and tx info message test data lists."""

    def _load_kafka_msg_dump(fpath):
        with gzip.open(fpath) as fp, jsonlines.Reader(fp) as json_lines:
            return [ConsumerRecord(**d) for d in json_lines]

    testdata_dir = Path(__file__).parent / "testdata"
    ops = _load_kafka_msg_dump(testdata_dir / "ops.jsonl.gz")
    tx_info = _load_kafka_msg_dump(testdata_dir / "tx_info.jsonl.gz")
    yield SimpleNamespace(ops=ops, tx_info=tx_info)
