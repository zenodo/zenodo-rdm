// This file is part of InvenioRDM
// Copyright (C) 2026 CERN.
//
// Zenodo RDM is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

import React, { Component } from "react";
import PropTypes from "prop-types";
import { Button, Popup } from "semantic-ui-react";
import { connect as connectFormik } from "formik";
import { connect } from "react-redux";
import _get from "lodash/get";
import { http } from "react-invenio-forms";
import { i18next } from "@translations/invenio_app_rdm/i18next";

class WorkflowButtonComponent extends Component {
  hasAllCompletedFiles = () => {
    const { fileEntries } = this.props;
    const files = Object.values(fileEntries ?? {});
    return files.length > 0 && files.every((file) => file.status === "finished");
  };

  isDisabled = (values, isSubmitting) => {
    const { disabled, isLoading } = this.props;
    if (disabled || isLoading || isSubmitting) return true;
    const filesEnabled = _get(values, "files.enabled", false);
    return filesEnabled && !this.hasAllCompletedFiles();
  };

  handleClick = async () => {
    const { record, formik, onWorkflowStart, onStreamStart, onError } = this.props;
    const recordId = record?.id ?? formik?.values?.id;

    if (!recordId) {
      onError(i18next.t("Could not determine record ID."));
      return;
    }

    // sets isLoading state
    onWorkflowStart();

    try {
      const response = await http.post(`/uploads/${recordId}/orcha`);
      const { workflowId, streamUrl } = response.data;
      if (!workflowId) {
        onError(i18next.t("Orcha did not respond with a workflow ID."));
        return;
      }
      if (!streamUrl) {
        onError(i18next.t("Orcha did not respond with a streaming endpoint."));
        return;
      }
      const source = new EventSource(streamUrl);
      onStreamStart(source);
    } catch (err) {
      onError(
        err?.response?.data?.error ??
          i18next.t(
            "An error occurred when trying to extract metadata from your files."
          )
      );
    }
  };

  render() {
    const { formik, isLoading, success } = this.props;
    const { values, isSubmitting } = formik;
    const isButtonDisabled = this.isDisabled(values, isSubmitting);

    let popupContent;
    if (isLoading) {
      popupContent = i18next.t("Extracting metadata...");
    } else if (isButtonDisabled) {
      popupContent = i18next.t("Upload at least one file first.");
    } else {
      popupContent = i18next.t("Extract metadata from your uploaded files.");
    }

    return (
      <Popup
        content={popupContent}
        trigger={
          <span>
            <Button
              fluid
              type="button"
              onClick={this.handleClick}
              disabled={isButtonDisabled}
              loading={isLoading}
              primary
              labelPosition="left"
              icon={success ? "check" : "magic"}
              content={
                success
                  ? i18next.t("Metadata extracted!")
                  : i18next.t("Extract Metadata")
              }
              aria-label={i18next.t("Extract Metadata")}
            />
          </span>
        }
      />
    );
  }
}

WorkflowButtonComponent.propTypes = {
  disabled: PropTypes.bool,
  isLoading: PropTypes.bool,
  success: PropTypes.bool,
  record: PropTypes.object.isRequired,
  formik: PropTypes.object.isRequired,
  fileEntries: PropTypes.object.isRequired,
  onWorkflowStart: PropTypes.func.isRequired,
  onStreamStart: PropTypes.func.isRequired,
  onError: PropTypes.func.isRequired,
};

WorkflowButtonComponent.defaultProps = {
  disabled: false,
  isLoading: false,
  success: false,
};

const mapStateToProps = (state) => ({
  fileEntries: state.files?.entries ?? {},
});

export const WorkflowButton = connect(
  mapStateToProps,
  null
)(connectFormik(WorkflowButtonComponent));
