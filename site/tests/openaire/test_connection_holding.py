# SPDX-FileCopyrightText: 2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later

from unittest.mock import MagicMock, patch

from sqlalchemy import event
from sqlalchemy.orm import Session

from zenodo_rdm.openaire.tasks import openaire_direct_index


class TransactionProbe:
    """"""

    DML = ("SELECT", "INSERT", "UPDATE", "DELETE")

    def __init__(self, engine):
        """Create a probe for ``engine``."""
        self._engine = engine
        self.log = []  # ("sql", statement) | ("end", "after_commit"|"after_rollback")

    def _on_sql(self, conn, cursor, statement, parameters, context, executemany):
        if statement.lstrip().split(None, 1)[0].upper() in self.DML:
            self.log.append(("sql", statement))

    def _on_commit(self, session):
        self.log.append(("end", "after_commit"))

    def _on_rollback(self, session):
        self.log.append(("end", "after_rollback"))

    def __enter__(self):
        """Attach the listeners."""
        event.listen(self._engine, "before_cursor_execute", self._on_sql)
        # Session-level events fire on session.commit/rollback the calls
        # that release the connection in production but not for inner
        # `with db.session.begin_nested` blocks, which do not release it
        event.listen(Session, "after_commit", self._on_commit)
        event.listen(Session, "after_rollback", self._on_rollback)
        return self

    def __exit__(self, *exc):
        """Detach the listeners."""
        event.remove(self._engine, "before_cursor_execute", self._on_sql)
        event.remove(Session, "after_commit", self._on_commit)
        event.remove(Session, "after_rollback", self._on_rollback)


def test_openaire_direct_index_holds_transaction_across_post(
    running_app, db, openaire_record, enable_openaire_indexing
):
    """`records_service.read()` opens the transaction, the POST runs inside it.

    The task never releases the transaction itself, only the Celery
    app-context teardown does, after the task body returns.
    """
    at_post = {}

    class Response(MagicMock):
        ok, status_code, text = True, 200, ""

    def post_probe(url, **kwargs):
        at_post["log"] = list(probe.log)
        return Response()

    with TransactionProbe(db.engine) as probe, patch(
        "zenodo_rdm.openaire.utils.Session"
    ) as session_cls:
        session_cls.return_value.post = MagicMock(side_effect=post_probe)
        openaire_direct_index.delay(openaire_record.id)  # eager in tests

    assert "log" in at_post, "POST was never called"
    assert at_post["log"][-1] == ("end", "after_commit")
