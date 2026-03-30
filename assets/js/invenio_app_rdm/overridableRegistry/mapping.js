// SPDX-FileCopyrightText: 2023 CERN
// SPDX-License-Identifier: GPL-3.0-or-later
import { UpgradeLegacyRecordButton } from "../../components/landing_page/overrides/UpgradeLegacyRecordButton";
import SubcommunityCreateForm from "../../components/community/overrides/SubcommunityCreateForm";
import FileModificationModalMessage from "../../components/community/overrides/FileModificationModalMessage";
import { CustomAffiliationsSuggestions } from "../../components/react_invenio_forms/CustomAffiliationsSuggestions";

export const overriddenComponents = {
  "InvenioAppRdm.RecordLandingPage.RecordManagement.container":
    UpgradeLegacyRecordButton,
  "ReactInvenioForms.AffiliationsSuggestions.content": CustomAffiliationsSuggestions,
  "InvenioCommunities.CommunityCreateForm.layout": SubcommunityCreateForm,
  "InvenioAppRdm.Deposit.ModificationModal.message": FileModificationModalMessage,
};
