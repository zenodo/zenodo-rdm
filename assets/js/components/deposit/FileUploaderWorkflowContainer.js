import React from "react";
import PropTypes from "prop-types";
import { FileUploader } from "@js/invenio_rdm_records";
import { SuggestionsButton } from "@js/invenio_app_rdm/deposit/orcha";

const hasOrchaConfig = (config) =>
  config?.orcha_enabled !== undefined || config?.orchaEnabled !== undefined;

const isOrchaEnabled = (config) => {
  const configValue = config?.orcha_enabled ?? config?.orchaEnabled;
  if (configValue !== undefined) return Boolean(configValue);

  if (typeof document === "undefined") return false;
  return JSON.parse(document.getElementById("orcha-enabled")?.dataset.value ?? "false");
};

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
    {!hasOrchaConfig(config) && !record.is_published && isOrchaEnabled(config) && (
      <SuggestionsButton record={record} />
    )}
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
