# SPDX-FileCopyrightText: 2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later


BASE_URL = "https://127.0.0.1:5000"
WAITLIST_URL = f"{BASE_URL}/ai-assist-features-waitlist"
STATUS_URL = f"{BASE_URL}/ai-assist-features-waitlist/status"


def _login(client, user_id):
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user_id)
        sess["_fresh"] = True


def test_unverified_cannot_see_or_join(client, app, UserFixture, db):
    """Authenticated but verified_at is None."""
    app.config["RDM_ORCHA_WAITLIST_ENABLED"] = True
    u = UserFixture(email="test@mail.org", password="123456", base_url=BASE_URL)
    u.create(app, db)
    _login(client, u.user.id)

    assert client.post(WAITLIST_URL).status_code == 404
    assert client.get(WAITLIST_URL).status_code == 404
    assert client.get(STATUS_URL).json["show_banner"] == False


def test_verified_user_cannot_see_if_not_waitlist_enabled(client, app, verified_user):
    """Verified user but no waitlist enabled."""
    app.config["RDM_ORCHA_WAITLIST_ENABLED"] = False
    verified_user.login(client)
    assert client.post(WAITLIST_URL).status_code == 404
    assert client.get(WAITLIST_URL).status_code == 404
    assert client.get(STATUS_URL).json["show_banner"] == False


def test_all_good_but_role_was_not_created(client, app, verified_user):
    """If someone tries to register when role is not created but page is online."""
    app.config["RDM_ORCHA_WAITLIST_ENABLED"] = True
    verified_user.login(client)
    assert client.post(WAITLIST_URL).status_code == 503


def test_verified_user_can_see_with_waitlist_enabled(
    client, app, verified_user, orcha_waitlist_role
):
    """Verified user and waitlist enabled."""
    app.config["RDM_ORCHA_WAITLIST_ENABLED"] = True
    verified_user.login(client)
    assert client.get(WAITLIST_URL).status_code == 200
    assert client.get(STATUS_URL).json["show_banner"] == True
    assert client.post(WAITLIST_URL).status_code == 302
    assert client.get(STATUS_URL).json["show_banner"] == False


def test_user_on_waitlist_blocks_banner_not_page(client, app, orcha_waitlisted_user):
    """Once the role is granted the page stays reachable (thank-you state).
    but the banner must never show again"""
    app.config["RDM_ORCHA_WAITLIST_ENABLED"] = True
    orcha_waitlisted_user.login(client)
    assert client.get(WAITLIST_URL).status_code == 200
    assert client.get(STATUS_URL).json["show_banner"] == False
