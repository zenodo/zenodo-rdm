import React from "react";
import PropTypes from "prop-types";
import { DepositFormApp } from "@js/invenio_rdm_records";
import { SuggestionsProvider } from "@js/invenio_app_rdm/deposit/orcha";

const hasOrchaConfig = (config) =>
  config?.orcha_enabled !== undefined || config?.orchaEnabled !== undefined;

const isOrchaEnabled = (config) => {
  const configValue = config?.orcha_enabled ?? config?.orchaEnabled;
  if (configValue !== undefined) return Boolean(configValue);

  if (typeof document === "undefined") return false;
  return JSON.parse(document.getElementById("orcha-enabled")?.dataset.value ?? "false");
};

export const OrchaDepositFormLayout = ({
  config,
  record,
  files,
  permissions,
  preselectedCommunity,
  recordSerializer,
  children,
}) => {
  const formApp = (
    <DepositFormApp
      config={config}
      record={record}
      files={files}
      permissions={permissions}
      preselectedCommunity={preselectedCommunity}
      recordSerializer={recordSerializer}
      errors={record.errors}
    >
      {children}
    </DepositFormApp>
  );
  return !hasOrchaConfig(config) && isOrchaEnabled(config) ? (
    <SuggestionsProvider>{formApp}</SuggestionsProvider>
  ) : (
    formApp
  );
};

OrchaDepositFormLayout.propTypes = {
  config: PropTypes.object.isRequired,
  record: PropTypes.object.isRequired,
  files: PropTypes.object,
  permissions: PropTypes.object,
  preselectedCommunity: PropTypes.object,
  recordSerializer: PropTypes.object,
  children: PropTypes.node,
};

OrchaDepositFormLayout.defaultProps = {
  files: undefined,
  permissions: undefined,
  preselectedCommunity: undefined,
  recordSerializer: undefined,
  children: null,
};
