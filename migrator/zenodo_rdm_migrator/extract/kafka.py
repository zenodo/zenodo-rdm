# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Kafka extraction classes."""

import json
from collections import Counter
from datetime import datetime
from pathlib import Path

import dictdiffer
from invenio_rdm_migrator.extract import Extract, Tx
from invenio_rdm_migrator.logging import Logger
from kafka import KafkaConsumer, TopicPartition
from sortedcontainers import SortedDict, SortedList


class TxState:
    """Transaction state."""

    def __init__(self, id, info=None):
        """Constructor."""
        self.id = id
        self.info = info
        # We order operations based on the Postgres LSN
        self.ops = SortedList(key=lambda o: o["source"]["lsn"])
        self._op_counts = Counter()

    @property
    def info(self):
        """Get transaction info."""
        return self._info

    @info.setter
    def info(self, val):
        """Set transaction info."""
        self._info = val  # store the raw value for debugging
        if val:
            # We only care about the table row counts stated in the transaction event
            self._info_counts = Counter(
                {
                    c["data_collection"]: c["event_count"]
                    for c in val["data_collections"]
                }
            )
        else:
            self._info_counts = None

    def append(self, op):
        """Add a single table row operation to the transaction state."""
        self.ops.add(op)

        # Update table row counts with the operations so far
        schema = op["source"]["schema"]
        table = op["source"]["table"]
        self._op_counts.update([f"{schema}.{table}"])

    @property
    def complete(self):
        """True if the available transaction info matches the ops table row counts."""
        return self.info is not None and self._info_counts == self._op_counts


def _load_json(val):
    if val:
        return json.loads(val.decode("utf-8"))


class KafkaExtractEnd(Exception):
    """Helper exception for signalling the end of a KafkaExtract."""


class KafkaExtract(Extract):
    """Extract Debezium change data capture stream via Kafka.

    .. code-block:: python

        # Example initialization
        extract = KafkaExtract(
            ops_topic="zenodo-migration.public",
            tx_topic="zenodo-migration.postgres_transaction",
            last_tx=563385187,
            from_ts=datetime.utcnow() - timedelta(minutes=5),
            config={
                "bootstrap_servers": [
                    "kafka01.server",
                    "kafka02.server",
                ],
                "security_protocol": "SASL_SSL",
                "sasl_mechanism": "GSSAPI",
            }
        )

    :param ops_topic: Kafka topic to consume statements/operations from.
    :param tx_topic: Kafka topic to consume transaction information from.
    :param config: Dictionary of extra configuration for the Kafka consumers.
    :param last_tx: Last transaction ID after which to start yielding.
    :param tx_buffer: How many transactions to buffer before starting to return. Larger
        values trade memory for safety.
    :param from_ts: Offset timestamp from which to start consuming messages from. If
        not passed we start consuming from the earliest possible offset.
    :param remove_unchanged_fields: If ``True``, removes unchanged fields for UPDATEs.
    :param _dump_dir: Path to dump consumed message to (useful for tests).
    """

    DEFAULT_CONSUMER_CFG = {
        "value_deserializer": _load_json,
        "key_deserializer": _load_json,
        # If we don't receive messages after 3sec, we stop (to try again later)
        "consumer_timeout_ms": 3000,
        # We will handle commiting offsets ourselves
        "enable_auto_commit": False,
        # We want to explicitly set the offsets we're starting from
        "auto_offset_reset": "none",
    }

    def __init__(
        self,
        *,
        ops_topic,
        tx_topic,
        last_tx,
        tx_buffer=10,
        config=None,
        from_ts=None,
        remove_unchanged_fields=True,
        _dump_dir=None,
    ):
        """Constructor."""
        self.ops_topic = ops_topic
        self.tx_topic = tx_topic
        if isinstance(from_ts, datetime):
            from_ts = int(from_ts.timestamp() * 1000)
        self.from_ts = from_ts
        assert last_tx is not None, "`last_tx` is required."
        self.last_tx = last_tx
        self.config = config or {}
        self.tx_registry = SortedDict({})
        self.tx_buffer = tx_buffer
        self.remove_unchanged_fields = remove_unchanged_fields
        self._last_yielded_tx = None
        self._topic_states = {}
        # TODO: This class probably needs a dedicated logger namespace
        self.logger = Logger.get_logger()
        self._dump_dir = Path(_dump_dir) if _dump_dir else None

    def _dump_msg(self, topic, msg):
        if self._dump_dir:
            outpath = Path(self._dump_dir) / (topic + ".jsonl")
            outpath.parent.mkdir(exist_ok=True, parents=True)
            # NOTE: Inefficient to open/close all the time, but is meant for development
            with outpath.open("a") as fout:
                fout.write(json.dumps(msg._asdict()) + "\n")

    def _seek_dt_offsets(self, consumer, topic, ts=None):
        """Seek/set offsets to the ."""
        partitions = {
            TopicPartition(topic, p): None for p in consumer.partitions_for_topic(topic)
        }
        consumer.assign(partitions)
        if ts:
            offsets = consumer.offsets_for_times({p: ts for p in partitions})
            partitions.update({p: o for p, (o, _) in offsets.items()})
        else:
            partitions = consumer.beginning_offsets(partitions)

        for partition, offset in partitions.items():
            consumer.seek(partition, offset)
        return partitions

    def _seek_committed_offsets(self, consumer, topic):
        partitions = [
            TopicPartition(topic, p) for p in consumer.partitions_for_topic(topic)
        ]
        offsets = [consumer.committed(p) for p in partitions]
        consumer.assign(partitions)
        for partition, offset in zip(partitions, offsets):
            consumer.seek(partition, offset)

    def _get_consumer(self, topic, group_id):
        consumer = KafkaConsumer(
            group_id=group_id,
            **self.DEFAULT_CONSUMER_CFG,
            **self.config,
        )
        if topic not in self._topic_states:
            self._topic_states[topic] = self._seek_dt_offsets(
                consumer,
                topic,
                ts=self.from_ts,
            )
        else:
            self._seek_committed_offsets(consumer, topic)
        return consumer

    # NOTE: These two properties are useful for tests/mocking
    @property
    def _tx_consumer(self):
        return self._get_consumer(self.tx_topic, "zenodo_migration_tx")

    @property
    def _ops_consumer(self):
        return self._get_consumer(self.ops_topic, "zenodo_migration_ops")

    def iter_tx_info(self):
        """Yield commited transactions info."""
        consumer = self._tx_consumer
        for tx_msg in consumer:
            self._dump_msg(self.tx_topic, tx_msg)

            if not tx_msg.value:
                # Sometimes messages don't contain a value... So far it's not been an
                # issue, but maybe logging in DEBUG could help at some point.
                self.logger.debug(f"No message value for tx_info {tx_msg}")
                consumer.commit()
                continue

            tx_id, lsn = map(int, tx_msg.value["id"].split(":"))
            # We don't yield anything before the configured last transaction ID
            if tx_id <= self.last_tx:
                consumer.commit()
                continue
            if tx_msg.value["status"] == "BEGIN":
                # ignore BEGIN statements
                consumer.commit()
                continue
            elif tx_msg.value["status"] == "END":
                consumer.commit()
                yield (tx_id, tx_msg.value)

    @staticmethod
    def _filter_unchanged_values(msg):
        # We don't have deeply nested dict values, since they are still raw JSON strings
        before = msg.value["before"]
        after = msg.value["after"]
        pk_keys = set(msg.key.keys())
        diff = dictdiffer.diff(before, after, ignore=pk_keys)
        changed_keys = {key for diff_op, key, _ in diff if diff_op == "change"}
        for key in (before.keys() | after.keys()) - (changed_keys | pk_keys):
            before.pop(key)
            after.pop(key)

    def iter_ops(self):
        """Yields operations/statements."""
        consumer = self._ops_consumer
        for op_msg in consumer:
            self._dump_msg(self.ops_topic, op_msg)

            if not op_msg.value:
                self.logger.debug(f"No message value for op {op_msg}")
                consumer.commit()
                continue
            tx_id = op_msg.value["source"]["txId"]
            if tx_id <= self.last_tx:
                consumer.commit()
                continue
            consumer.commit()

            if self.remove_unchanged_fields and op_msg.value["op"] == "u":
                self._filter_unchanged_values(op_msg)

            yield (tx_id, dict(key=op_msg.key, **op_msg.value))

    def _yield_completed_tx(self, min_batch=None):
        """Yields completed transactions."""
        completed_tx_batch = []
        for tx_state in self.tx_registry.values():
            if not tx_state.complete:
                # We stop at the first non-completed transaction
                break
            completed_tx_batch.append(tx_state)

            # if we reached the minimum batch size, we stop
            if min_batch and len(completed_tx_batch) == min_batch:
                break

        # If we didn't make a big enough batch we return
        if min_batch and len(completed_tx_batch) < min_batch:
            return

        for tx in completed_tx_batch:
            del self.tx_registry[tx.id]
            # Keep track of the last yielded transaction ID
            self._last_yielded_tx = tx.id
            yield Tx(id=tx.id, operations=list(tx.ops))

    def run(self):
        """Return a blocking generator yielding completed transactions."""
        # We're using an (always) SortedDict, since we want to yield transactions in
        # their correct order.
        try:
            while True:
                # First we consume all the available transactions information
                for tx_id, tx_info in self.iter_tx_info():
                    if tx_id in self.tx_registry:
                        self.tx_registry[tx_id].info = tx_info
                    else:
                        self.tx_registry[tx_id] = TxState(tx_id, tx_info)

                # We now consume operations and build on a (pending) transaction state.
                for tx_id, op in self.iter_ops():
                    tx_state = self.tx_registry.setdefault(tx_id, TxState(tx_id))
                    tx_state.append(op)
                    if tx_state.complete:
                        self.logger.info(f"Completed transaction {tx_state.id}")

                # If no new transactions, we don't need to sleep since consumers
                # have a timeout/sleep already via "consumer_timeout_ms".
                yield from self._yield_completed_tx(min_batch=self.tx_buffer)
        # Normally this extract would run forever, so we need some mechanism to stop
        except KafkaExtractEnd:
            # Yield any remaining completed transactions
            yield from self._yield_completed_tx()
