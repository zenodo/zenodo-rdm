// This file is part of InvenioRDM
// Copyright (C) 2023 CERN.
//
// Zenodo RDM is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

import React, { Component } from "react";
import { Button, Grid, Message, Icon } from "semantic-ui-react";
import PropTypes from "prop-types";
import { http, withCancel } from "react-invenio-forms";

export class UpgradeLegacyRecordButton extends Component {
  constructor(props) {
    super(props);
    this.state = {
      legacyRequestId: "",
      fetchRequestsError: undefined,
    };
  }

  componentDidMount() {
    const { record, currentUserId } = this.props;
    if (record.parent.access.owned_by.user === currentUserId) {
      this.fetchRequests();
    }
  }

  fetchRequests = async () => {
    const { record } = this.props;
    try {
      const cancellableFetch = withCancel(
        http.get(`${record.links.requests}?q=type:legacy-record-upgrade&is_open=true`, {
          headers: {
            Accept: "application/json",
          },
        })
      );

      const response = await cancellableFetch.promise;
      const result = response.data.hits;
      if (result.total > 0) {
        this.setState({ legacyRequestId: result.hits[0].id });
      }
    } catch (error) {
      let errorMessage = error.message;
      if (error.response) {
        errorMessage = error.response.data.message;
      }

      console.error(error);
      this.setState({ fetchRequestsError: errorMessage });
    }
  };

  render() {
    const { isPreviewSubmissionRequest } = this.props;
    const { legacyRequestId, fetchRequestsError } = this.state;
    return (
      <>
        {legacyRequestId && !isPreviewSubmissionRequest && (
          <Grid.Column className="pt-0">
            <Button
              fluid
              color="white"
              size="medium"
              onClick={() => (window.location = `/me/requests/${legacyRequestId}`)}
              icon
              labelPosition="left"
            >
              <Icon name="settings" />
              Upgrade legacy record
            </Button>
          </Grid.Column>
        )}
        {fetchRequestsError && (
          <Grid.Row className="record-management">
            <Grid.Column>
              <Message negative>{fetchRequestsError}</Message>
            </Grid.Column>
          </Grid.Row>
        )}
      </>
    );
  }
}

UpgradeLegacyRecordButton.propTypes = {
  isPreviewSubmissionRequest: PropTypes.bool.isRequired,
  record: PropTypes.object.isRequired,
  currentUserId: PropTypes.string.isRequired,
};
