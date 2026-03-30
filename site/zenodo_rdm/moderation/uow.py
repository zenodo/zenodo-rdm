# SPDX-FileCopyrightText: 2024 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Unit of work operations."""

from invenio_db.uow import Operation


# TODO: This should be moved to invenio-db or invenio-records-resources
class ExceptionOp(Operation):
    """Operation to perform cleanup logic for exceptions.

    This unit of work operation is initialied using another regular operation and maps
    the following methods to the associated "clean-up" unit of work lifecycle methods:

    - ``on_exception``: ``on_register``
    - ``on_rollback``: ``on_commit``
    - ``on_post_rollback``: ``on_post_commit``

    Additionally, it allows to specify an action function to be executed during the
    unit of work lifecycle if an exception is raised. This is to allow rolling back
    any transactions up to the point of the exception, while still performing some
    cleanup logic.
    """

    def __init__(self, commit_op, action_func=None):
        """Initialize exception operation."""
        self.action_func = action_func
        self.commit_op = commit_op

    def on_exception(self, uow, exception):
        """Perform action function if exception is raised."""
        if self.action_func:
            self.action_func(uow, exception)
        self.commit_op.on_register(uow)

    def on_rollback(self, uow):
        """Perform the commit operation on rollback."""
        self.commit_op.on_commit(uow)

    def on_post_rollback(self, uow):
        """Perform the post commit operation on post rollback."""
        self.commit_op.on_post_commit(uow)
