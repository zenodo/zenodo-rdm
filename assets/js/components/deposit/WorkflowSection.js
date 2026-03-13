// This file is part of InvenioRDM
// Copyright (C) 2026 CERN.
//
// Zenodo RDM is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

import React, { Component } from "react";
import PropTypes from "prop-types";
import { Grid, Message, Icon } from "semantic-ui-react";
import { WorkflowButton } from "./WorkflowButton";
import { WorkflowStreamAccordion } from "./WorkflowStreamAccordion";
import { i18next } from "@translations/invenio_app_rdm/i18next";

export class WorkflowSection extends Component {
  state = {
    isLoading: false,
    success: false,
    error: null,
    streamOutput: "",
    isStreaming: false,
  };

  componentWillUnmount() {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
  }

  eventSource = null;

  handleStreamStart = (source) => {
    // close existing sources when starting a new one
    if (this.eventSource) {
      this.eventSource.close();
    }
    this.eventSource = source;

    this.setState({
      isLoading: true,
      success: true,
      streamOutput: "",
      isStreaming: true,
    });

    source.onmessage = (event) => {
      this.setState((prev) => ({
        streamOutput: prev.streamOutput + event.data + "\n",
      }));
    };

    source.onerror = () => {
      source.close();
      this.eventSource = null;
      this.setState({
        isStreaming: false,
        isLoading: false,
        error: i18next.t(
          "An unexpected error occurred while streaming the workflow results."
        ),
      });
    };

    source.addEventListener("done", () => {
      source.close();
      this.eventSource = null;
      this.setState({ isStreaming: false, isLoading: false });
    });
  };

  handleError = (message) => {
    this.setState({ isLoading: false, error: message, success: false });
  };

  render() {
    const { record } = this.props;
    const { isLoading, success, error, streamOutput, isStreaming } = this.state;

    return (
      <Grid className="mt-10">
        <Grid.Row>
          <Grid.Column width={6} floated="right">
            <WorkflowButton
              record={record}
              isLoading={isLoading}
              success={success}
              onStreamStart={this.handleStreamStart}
              onError={this.handleError}
            />
          </Grid.Column>
        </Grid.Row>

        {error && (
          <Grid.Row>
            <Grid.Column width={6} floated="right">
              <Message
                negative
                size="small"
                onDismiss={() => this.setState({ error: null })}
              >
                <Icon name="warning circle" />
                {error}
              </Message>
            </Grid.Column>
          </Grid.Row>
        )}

        {streamOutput && (
          <Grid.Row>
            <Grid.Column width={16}>
              <WorkflowStreamAccordion
                streamOutput={streamOutput}
                isStreaming={isStreaming}
              />
            </Grid.Column>
          </Grid.Row>
        )}
      </Grid>
    );
  }
}

WorkflowSection.propTypes = {
  record: PropTypes.object.isRequired,
};
