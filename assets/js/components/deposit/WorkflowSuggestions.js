// This file is part of InvenioRDM
// Copyright (C) 2026 CERN.
//
// Zenodo RDM is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

import React, { Component } from "react";
import PropTypes from "prop-types";
import { Icon, Message } from "semantic-ui-react";
import { i18next } from "@translations/invenio_app_rdm/i18next";

const FIELD_LABELS = {
  title: i18next.t("Title"),
  description: i18next.t("Description"),
  publication_date: i18next.t("Publication date"),
  doi: i18next.t("DOI"),
  creators: i18next.t("Creators"),
};

export class WorkflowSuggestions extends Component {
  renderAuthor = (author) => (
    <>
      <div>
        <strong>{author.name}</strong>
      </div>
      {author.affiliation && <div>{author.affiliation}</div>}
      {author.orcid && <div>{author.orcid}</div>}
    </>
  );

  renderValue = (value) => {
    if (Array.isArray(value)) {
      return (
        <Message.List>
          {value.map((author, index) => (
            <Message.Item key={author.orcid ?? `${index}-${author.name}`}>
              {this.renderAuthor(author)}
            </Message.Item>
          ))}
        </Message.List>
      );
    }

    return value ?? i18next.t("Ops, no suggested value for this field.");
  };

  render() {
    const { suggestions } = this.props;

    return (
      <div className="panel">
        {suggestions.map(({ field, value }, index) => (
          <Message key={field || index} info size="small">
            <Message.Content>
              <Message.Header icon>
                <Icon name="check circle outline" />
                {FIELD_LABELS[field] ?? field}
              </Message.Header>
              <div>{this.renderValue(value)}</div>
            </Message.Content>
          </Message>
        ))}
      </div>
    );
  }
}

const authorShape = PropTypes.shape({
  name: PropTypes.string.isRequired,
  affiliation: PropTypes.string,
  orcid: PropTypes.string,
});

WorkflowSuggestions.propTypes = {
  suggestions: PropTypes.arrayOf(
    PropTypes.shape({
      field: PropTypes.string.isRequired,
      value: PropTypes.oneOfType([PropTypes.string, PropTypes.arrayOf(authorShape)]),
    })
  ).isRequired,
};
