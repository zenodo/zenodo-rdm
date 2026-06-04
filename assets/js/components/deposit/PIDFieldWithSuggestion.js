import React, { Fragment } from "react";
import PropTypes from "prop-types";
import { PIDField } from "@js/invenio_rdm_records";
import { FieldSuggestion } from "@js/invenio_app_rdm/deposit/orcha";

export const PIDFieldWithSuggestion = ({ config, record }) => (
  <Fragment>
    {config.pids.map((pid) => (
      <Fragment key={pid.scheme}>
        <PIDField
          btnLabelDiscardPID={pid.btn_label_discard_pid}
          btnLabelGetPID={pid.btn_label_get_pid}
          canBeManaged={pid.can_be_managed}
          canBeUnmanaged={pid.can_be_unmanaged}
          optionalDOItransitions={pid.optional_doi_transitions}
          fieldPath={`pids.${pid.scheme}`}
          fieldLabel={pid.field_label}
          isEditingPublishedRecord={record.is_published === true}
          managedHelpText={pid.managed_help_text}
          pidLabel={pid.pid_label}
          pidPlaceholder={pid.pid_placeholder}
          pidType={pid.scheme}
          unmanagedHelpText={pid.unmanaged_help_text}
          doiDefaultSelection={pid.default_selected}
          required={config.is_doi_required}
          record={record}
        />
        {pid.scheme === "doi" && <FieldSuggestion field="doi" />}
      </Fragment>
    ))}
  </Fragment>
);

PIDFieldWithSuggestion.propTypes = {
  config: PropTypes.object.isRequired,
  record: PropTypes.object.isRequired,
};
