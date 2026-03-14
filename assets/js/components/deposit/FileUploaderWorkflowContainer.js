// This file is part of InvenioRDM
// Copyright (C) 2026 CERN.
//
// Zenodo RDM is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

import React from "react";
import PropTypes from "prop-types";
import { WorkflowSection } from "./WorkflowSection";
import { FileUploader } from "@js/invenio_rdm_records";

export const FileUploaderWorkflowContainer = ({
  record,
  config,
  permissions,
  filesLocked,
  allowEmptyFiles,
}) => (
  <>
    <FileUploader
      isDraftRecord={!record.is_published}
      quota={config.quota}
      decimalSizeDisplay={config.decimal_size_display}
      showMetadataOnlyToggle={permissions?.can_manage_files}
      allowEmptyFiles={allowEmptyFiles}
      filesLocked={filesLocked}
    />
    <WorkflowSection record={record} />
  </>
);

FileUploaderWorkflowContainer.propTypes = {
  record: PropTypes.object.isRequired,
  config: PropTypes.object.isRequired,
  permissions: PropTypes.object,
  filesLocked: PropTypes.bool,
  allowEmptyFiles: PropTypes.bool,
};

FileUploaderWorkflowContainer.defaultProps = {
  permissions: null,
  filesLocked: false,
  allowEmptyFiles: false,
};
