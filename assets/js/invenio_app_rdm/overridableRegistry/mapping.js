// This file is part of InvenioRDM
// Copyright (C) 2023 CERN.
//
// Zenodo RDM is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

import { UpgradeLegacyRecordButton } from "../../components/landing_page/overrides/UpgradeLegacyRecordButton";
import { FileUploaderNewVersion } from "../../components/landing_page/overrides/FileUploaderNewVersion";
import SubcommunityCreateForm from "../../components/community/overrides/SubcommunityCreateForm";

export const overriddenComponents = {
  "InvenioAppRdm.RecordLandingPage.RecordManagement.container":
    UpgradeLegacyRecordButton,
  "ReactInvenioDeposit.FileUploader.NewVersionButton.container": FileUploaderNewVersion,
  "InvenioCommunities.CommunityCreateForm.layout": SubcommunityCreateForm
};
