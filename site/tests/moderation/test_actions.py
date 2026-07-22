# SPDX-FileCopyrightText: 2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests for moderation actions."""

from unittest.mock import MagicMock, patch

import pytest
from invenio_users_resources.proxies import current_actions_registry
from invenio_users_resources.services.users.tasks import execute_moderation_actions

from zenodo_rdm.moderation.actions import on_block_notify


def test_block_triggers_notification(app, db, UserFixture, monkeypatch):
    """on_block_notify is called and sends an email when execute_moderation_actions runs."""
    u = UserFixture(email="blocked@example.com", password="blockeduser")
    u.create(app, db)

    monkeypatch.setitem(current_actions_registry, "block", [on_block_notify])

    with app.extensions["mail"].record_messages() as outbox:
        execute_moderation_actions(user_id=u.user.id, action="block")

        assert len(outbox) == 1
        msg = outbox[0]
        assert msg.subject == "Notice of account suspension on Zenodo"
        assert msg.recipients == ["blocked@example.com"]
        assert msg.sender == app.config["MAIL_DEFAULT_SENDER"]
        assert msg.reply_to == app.config["MAIL_DEFAULT_SUPPORT"]
        assert msg.body.startswith("Dear user,")


@pytest.fixture()
def blocked_user():
    """Mock UserAggregate for a blocked user."""
    user = MagicMock()
    user.id = 123
    user.email = "blocked@example.com"
    user.profile = {"full_name": "Jane Doe"}
    return user


def test_actor_triggered_block_sends_no_email(app, blocked_user):
    """Human-triggered block (actor_id set) does not send an email."""
    with patch(
        "zenodo_rdm.moderation.actions.UserAggregate.get_record",
        return_value=blocked_user,
    ):
        with app.extensions["mail"].record_messages() as outbox:
            on_block_notify(user_id=blocked_user.id, actor_id=456)

    assert len(outbox) == 0
