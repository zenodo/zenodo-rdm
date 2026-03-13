// This file is part of InvenioRDM
// Copyright (C) 2026 CERN.
//
// Zenodo RDM is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

import React, { Component } from "react";
import PropTypes from "prop-types";
import { Accordion, Icon } from "semantic-ui-react";
import { i18next } from "@translations/invenio_app_rdm/i18next";

export class WorkflowStreamAccordion extends Component {
  state = { active: true };

  render() {
    const { streamOutput, isStreaming } = this.props;
    const { active } = this.state;

    if (!streamOutput) return null;

    return (
      <Accordion className="panel mt-10">
        <Accordion.Title
          className="panel-heading"
          active={active}
          onClick={() => this.setState((p) => ({ active: !p.active }))}
        >
          <Icon name="angle right" className="mr-5" />
          {isStreaming
            ? i18next.t("Extracting metadata…")
            : i18next.t("Extraction result")}
        </Accordion.Title>
        <Accordion.Content active={active}>
          <pre className="text-sm text-gray-100 ml-10">{streamOutput}</pre>
        </Accordion.Content>
      </Accordion>
    );
  }
}

WorkflowStreamAccordion.propTypes = {
  streamOutput: PropTypes.string.isRequired,
  isStreaming: PropTypes.bool.isRequired,
};
