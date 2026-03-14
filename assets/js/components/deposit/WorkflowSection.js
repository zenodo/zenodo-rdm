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
    status: "idle",
    error: null,
    streamOutput: "",
  };

  componentWillUnmount() {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
    this.clearStreamTimeout();
  }

  startStreamTimeout = (source) => {
    return setTimeout(() => {
      source.close();
      this.eventSource = null;
      this.setState({
        status: "error",
        error: i18next.t("Workflow timed out."),
      });
    }, 60 * 1000);
  };

  clearStreamTimeout = () => {
    if (this.streamTimeoutId) {
      clearTimeout(this.streamTimeoutId);
      this.streamTimeoutId = null;
    }
  };

  eventSource = null;
  streamTimeoutId = null;

  handleWorkflowStart = () => {
    this.setState({
      status: "triggering-workflow",
      streamOutput: "",
      error: null,
    });
  };

  handleStreamStart = (source) => {
    // close existing sources when starting a new one
    if (this.eventSource) {
      this.eventSource.close();
    }
    this.eventSource = source;

    this.setState({
      status: "streaming",
    });

    this.clearStreamTimeout();
    this.streamTimeoutId = this.startStreamTimeout(source);

    source.onmessage = (event) => {
      this.clearStreamTimeout();
      this.streamTimeoutId = this.startStreamTimeout(source);
      this.setState((prev) => ({
        streamOutput: prev.streamOutput + event.data + "\n",
      }));
    };

    source.onerror = () => {
      this.clearStreamTimeout();
      source.close();
      this.eventSource = null;
      this.setState({
        status: "error",
        error: i18next.t(
          "An unexpected error occurred while streaming the workflow results."
        ),
      });
    };

    source.addEventListener("done", () => {
      this.clearStreamTimeout();
      source.close();
      this.eventSource = null;
      this.setState({ status: "success" });
    });
  };

  handleError = (message) => {
    this.clearStreamTimeout();
    this.setState({ error: message, status: "error" });
  };

  render() {
    const { record } = this.props;
    const { status, error, streamOutput } = this.state;
    const isLoading = status === "triggering-workflow" || status === "streaming";

    return (
      <Grid className="mt-10">
        <Grid.Row>
          <Grid.Column width={6} floated="right">
            <WorkflowButton
              record={record}
              isLoading={isLoading}
              success={status === "success"}
              onWorkflowStart={this.handleWorkflowStart}
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
                isStreaming={status === "streaming"}
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
