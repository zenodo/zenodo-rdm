import React from "react";
import PropTypes from "prop-types";
import { FileUploader } from "@js/invenio_rdm_records";
import { SuggestionsButton } from "@js/invenio_app_rdm/deposit/orcha";

export const FileUploaderWorkflowContainer = ({
  record,
  config,
  permissions,
  filesLocked,
  allowEmptyFiles,
  fileActions,
}) => {
  const orchaEnabled = Boolean(config?.orcha_enabled ?? config?.orchaEnabled);

  const filename = record?.name?.toLowerCase() ?? "";

  const orchaFileActions =
    fileActions ||
    (!record.is_published && orchaEnabled ? (
      record?.mimetype === "application/pdf" || filename.endsWith(".pdf") ? null : (
        <SuggestionsButton record={record} file={record} />
      )
    ) : undefined);

  return (
    <FileUploader
      isDraftRecord={!record.is_published}
      quota={config.quota}
      decimalSizeDisplay={config.decimal_size_display}
      showMetadataOnlyToggle={permissions?.can_manage_files}
      allowEmptyFiles={allowEmptyFiles}
      filesLocked={filesLocked}
      fileActions={orchaFileActions}
    />
  );
};

FileUploaderWorkflowContainer.propTypes = {
  record: PropTypes.object.isRequired,
  config: PropTypes.object.isRequired,
  permissions: PropTypes.object,
  filesLocked: PropTypes.bool,
  allowEmptyFiles: PropTypes.bool,
  fileActions: PropTypes.func,
};

FileUploaderWorkflowContainer.defaultProps = {
  permissions: null,
  filesLocked: false,
  allowEmptyFiles: false,
  fileActions: undefined,
};
