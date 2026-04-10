# SPDX-FileCopyrightText: 2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Policies for self-service user actions."""

from invenio_i18n import lazy_gettext as _
from invenio_rdm_records.proxies import current_rdm_records_storage_service
from invenio_rdm_records.services.request_policies import BasePolicy


class QuotaIncreasePolicy(BasePolicy):
    """Quota increase policy."""

    id = "quota-increase-policy-v1"
    description = _("You can increase the quota of your drafts.")

    def is_allowed(self, identity, record):
        """Only owners can increase the quota."""
        if identity.user.verified_at:
            if record:
                is_record_owner = (
                    identity.user.id == record.parent.access.owned_by.owner_id
                )
                return is_record_owner
            else:
                # unsaved drafts are always valid as you are the owner
                # i.e. you can't share an unsaved draft to someone else
                return True
        return False

    def evaluate(self, identity, record):
        """
        Check if record can be increased by specific additional quota for this user.

        Only used on backend. The frontend evaluates is allowed in setAdditionalQuota.
        """
        min_additional_quota_value = (
            current_rdm_records_storage_service.min_additional_quota_value(
                identity.id, record
            )
        )
        additional_storage = current_rdm_records_storage_service.additional_storage(
            identity.id, record
        )
        max_additional_quota_value = (
            current_rdm_records_storage_service.max_additional_quota_value(
                identity.id, record
            )
        )

        return (
            min_additional_quota_value
            <= additional_storage
            <= max_additional_quota_value
        )
