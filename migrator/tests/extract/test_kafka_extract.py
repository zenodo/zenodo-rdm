# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Migrator tests configuration."""

import copy
import itertools
import random
from collections import Counter
from types import SimpleNamespace
from unittest.mock import PropertyMock

from invenio_rdm_migrator.extract import Tx

from zenodo_rdm_migrator.extract import KafkaExtract, KafkaExtractEnd


def _random_chunks(li, min_chunk=1, max_chunk=50):
    it = iter(li)
    while True:
        nxt = list(itertools.islice(it, random.randint(min_chunk, max_chunk)))
        if nxt:
            yield nxt
        else:
            break


class MockConsumer(list):
    """Mock Kafka consumer iterator."""

    def commit(self):
        pass


def _patch_consumers(mocker, tx_info, ops):
    """Helper for patching consumers of ``KafkaExtract``."""
    mocker.patch.object(
        KafkaExtract,
        "_tx_consumer",
        side_effect=[*tx_info, MockConsumer([]), KafkaExtractEnd],
        new_callable=PropertyMock,
    )
    mocker.patch.object(
        KafkaExtract,
        "_ops_consumer",
        side_effect=[*ops, MockConsumer([]), KafkaExtractEnd],
        new_callable=PropertyMock,
    )


FIRST_TX_OP_COUNTS = (
    563388798,
    {
        "public.oauth2server_token": 1,
        "public.records_metadata": 1,
    },
)
LAST_TX_OP_COUNTS = (
    563390849,
    {
        "public.pidstore_pid": 8,
        "public.files_bucket": 5,
        "public.records_metadata": 3,
        "public.files_files": 2,
        "public.files_object": 2,
        "public.records_buckets": 1,
        "public.communities_community_record": 1,
        "public.pidstore_redirect": 1,
        "public.pidrelations_pidrelation": 1,
    },
)
MIDDLE_TX_OP_COUNTS = (
    563390343,
    {
        "public.files_bucket": 2,
        "public.files_files": 2,
        "public.files_object": 2,
        "public.oauth2server_token": 1,
        "public.records_metadata": 1,
    },
)


def _assert_op_counts(tx, expected_counts):
    op_counts = Counter(
        [f'{op["source"]["schema"]}.{op["source"]["table"]}' for op in tx.operations]
    )
    assert op_counts == expected_counts


def _assert_result(
    result,
    *,
    count,
    first_tx_id,
    last_tx_id,
    extra_tx_ids=None,
    excluded_tx_ids=None,
    tx_op_counts=None,
):
    assert len(result) == count
    assert all(isinstance(t, Tx) for t in result)
    tx_dict = {t.id: t for t in result}
    tx_ids = list(tx_dict.keys())
    assert tx_ids[0] == first_tx_id
    assert tx_ids[-1] == last_tx_id
    assert set(extra_tx_ids or []) <= set(tx_ids)
    assert len(set(excluded_tx_ids or []).intersection(set(tx_ids))) == 0
    for tx_id, op_counts in (tx_op_counts or {}).items():
        _assert_op_counts(tx_dict[tx_id], op_counts)


def test_kafka_data(kafka_data):
    """Test sample data basic attributes."""
    assert len(kafka_data.ops) == 1820
    assert len(kafka_data.tx_info) == 282


def test_simple_extract(mocker, kafka_data):
    """Test a simple run over a single uninterrupted iteration of messages.

    "Uninterrupted" means that the Kafka consumers yield all the available messages on
    their first iteration. This is not a very realistic scenario, since normally
    messages arrive in random-sized batches to Kafka topics, and are consumed in a
    somewhat "messy" order. It still serves as a good base case.
    """
    _patch_consumers(
        mocker,
        [MockConsumer(kafka_data.tx_info)],
        [MockConsumer(kafka_data.ops)],
    )

    extract = KafkaExtract(
        ops_topic="test_topic",
        tx_topic="test_topic",
        # first transaction ID in the file, will be skipped
        last_tx=563388795,
    )
    result = list(extract.run())
    _assert_result(
        result,
        count=140,
        first_tx_id=563388798,
        last_tx_id=563390849,
        excluded_tx_ids=(563388795,),
        tx_op_counts=dict([FIRST_TX_OP_COUNTS, MIDDLE_TX_OP_COUNTS, LAST_TX_OP_COUNTS]),
    )


def test_randomized_extract(mocker, kafka_data):
    """Test single uninterrupted iteration of random order messages.

    This should work since in the context of a single run, the order of transactions is
    maintained.
    """
    shuffled_tx_info = random.sample(kafka_data.tx_info, len(kafka_data.tx_info))
    shuffled_ops = random.sample(kafka_data.ops, len(kafka_data.ops))
    _patch_consumers(
        mocker,
        [MockConsumer(shuffled_tx_info)],
        [MockConsumer(shuffled_ops)],
    )

    extract = KafkaExtract(
        ops_topic="test_topic",
        tx_topic="test_topic",
        last_tx=563388795,
    )
    result = list(extract.run())
    _assert_result(
        result,
        count=140,
        first_tx_id=563388798,
        last_tx_id=563390849,
        excluded_tx_ids=(563388795,),
        tx_op_counts=dict([FIRST_TX_OP_COUNTS, MIDDLE_TX_OP_COUNTS, LAST_TX_OP_COUNTS]),
    )


def test_random_sized_batches_extract(mocker, kafka_data):
    """Test random-sized batches of messages.

    Here we randomize the number of messages returned by each consumer. This is fine as
    long as we don't end up in a scenario where a very old transaction comes out of
    order (specifically >=10 transactions later)

    In theory this can be avoided though by setting the ``tx_buffer`` option of
    ``KafkaExtract`` to a higher value.
    """
    # NOTE: We create the same number of total batches for both types
    tx_info_batches, ops_batches = zip(
        *itertools.zip_longest(
            [MockConsumer(c) for c in _random_chunks(kafka_data.tx_info)],
            [MockConsumer(c) for c in _random_chunks(kafka_data.ops)],
            fillvalue=MockConsumer([]),
        )
    )
    _patch_consumers(
        mocker,
        tx_info_batches,
        ops_batches,
    )
    extract = KafkaExtract(
        ops_topic="test_topic",
        tx_topic="test_topic",
        # first transaction ID in the file, will be skipped
        last_tx=563388795,
    )
    result = list(extract.run())
    _assert_result(
        result,
        count=140,
        first_tx_id=563388798,
        last_tx_id=563390849,
        excluded_tx_ids=(563388795,),
        tx_op_counts=dict([FIRST_TX_OP_COUNTS, MIDDLE_TX_OP_COUNTS, LAST_TX_OP_COUNTS]),
    )


def test_later_last_tx(mocker, kafka_data):
    """Test passing a later transaction ID from the stream.

    In this case we should just get less transactions processed, but still they should
    be whole (since we go through all messages, but just discard any that have a
    smaller transaction ID).
    """
    _patch_consumers(
        mocker,
        [MockConsumer(kafka_data.tx_info)],
        [MockConsumer(kafka_data.ops)],
    )

    extract = KafkaExtract(
        ops_topic="test_topic",
        tx_topic="test_topic",
        # a later transaction in the file
        last_tx=563389290,
    )
    result = list(extract.run())
    _assert_result(
        result,
        count=102,
        first_tx_id=563389293,
        last_tx_id=563390849,
        excluded_tx_ids=(
            563388798,
            563389290,
        ),
        tx_op_counts=dict([MIDDLE_TX_OP_COUNTS, LAST_TX_OP_COUNTS]),
    )


def test_unchanged_fields(mocker):
    """Test the unchanged fields filtering for UPDATEs."""
    tx_info = {
        "key": {"id": "563388795:1461026653952"},
        "value": {
            "status": "END",
            "id": "563388795:1461026653952",
            "event_count": 1,
            "data_collections": [
                {"data_collection": "public.files_bucket", "event_count": 1},
            ],
            "ts_ms": 1691761684209,
        },
    }
    op = {
        "key": {
            "id": "2c5e1797-e030-40e2-b32f-99335730a39d",
        },
        "value": {
            "before": {
                "created": 1691761300019002,
                "updated": 1691761300044346,
                "id": "2c5e1797-e030-40e2-b32f-99335730a39d",
                "default_location": 1,
                "default_storage_class": "S",
                "size": 10_000,
                "quota_size": 50_000_000_000,
                "max_file_size": None,
                "locked": False,
                "deleted": False,
            },
            "after": {
                "created": 1691761300019002,
                "updated": 1691761683566267,
                "id": "2c5e1797-e030-40e2-b32f-99335730a39d",
                "default_location": 1,
                "default_storage_class": "S",
                "size": 50_000,
                "quota_size": 50_000_000_000,
                "max_file_size": None,
                "locked": False,
                "deleted": False,
            },
            "source": {
                "ts_ms": 1691761684209,
                "schema": "public",
                "table": "files_bucket",
                "txId": 563388795,
                "lsn": 1461026601320,
            },
            "op": "u",
            "ts_ms": 1691761684705,
        },
    }

    _patch_consumers(
        mocker,
        [MockConsumer([SimpleNamespace(**copy.deepcopy(tx_info))])],
        [MockConsumer([SimpleNamespace(**copy.deepcopy(op))])],
    )

    extract = KafkaExtract(
        ops_topic="test_topic",
        tx_topic="test_topic",
        last_tx=0,
        remove_unchanged_fields=False,
    )
    result = list(extract.run())
    assert len(result) == 1
    before = result[0].operations[0]["before"]
    after = result[0].operations[0]["after"]
    original_keys = op["value"]["after"].keys()
    # No keys have been changed
    assert before.keys() == after.keys() == original_keys

    # Patch again for a re-run
    _patch_consumers(
        mocker,
        [MockConsumer([SimpleNamespace(**copy.deepcopy(tx_info))])],
        [MockConsumer([SimpleNamespace(**copy.deepcopy(op))])],
    )
    extract.remove_unchanged_fields = True
    result = list(extract.run())
    assert len(result) == 1
    before = result[0].operations[0]["before"]
    after = result[0].operations[0]["after"]
    # Only "size" and "updated" changed. "id" is the PK, so it also stays
    assert before.keys() == after.keys() == {"id", "updated", "size"}
