// This file is part of InvenioRDM
// Copyright (C) 2026 CERN.
//
// Zenodo RDM is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.
import React, { Component } from "react";
import PropTypes from "prop-types";
import { Button } from "semantic-ui-react";
import { connect as connectFormik } from "formik";
import { i18next } from "@translations/invenio_app_rdm/i18next";

const creatorField = (creator) => ({
  person_or_org: {
    type: "personal",
    family_name: creator.name.split(", ")[0] ?? creator.name,
    given_name: creator.name.split(", ")[1] ?? "",
    identifiers: creator.orcid ? [{ identifier: creator.orcid, scheme: "orcid" }] : [],
  },
  affiliations: creator.affiliation ? [{ name: creator.affiliation }] : [],
  role: "",
});

class ApplySuggestionButtonComponent extends Component {
  state = { filledSuggestions: null };

  applySuggestionToFormik = (field, value, formik) => {
    switch (field) {
      case "creators":
        formik.setFieldValue("metadata.creators", value.map(creatorField));
        break;
      case "doi":
        formik.setFieldValue("pids.doi", { identifier: value, provider: "external" });
        break;
      default:
        formik.setFieldValue(`metadata.${field}`, value);
    }
  };

  handleClick = () => {
    const { formik, suggestions } = this.props;

    // separate description from other fields as it requires resetting the form
    const descriptionSuggestion = suggestions.find(
      ({ field }) => field === "description"
    );
    if (descriptionSuggestion) {
      formik.resetForm({
        values: {
          ...formik.values,
          metadata: {
            ...formik.values.metadata,
            description: `<p>${descriptionSuggestion["value"]}</p>`,
          },
        },
      });
    }

    const otherSuggestions = suggestions.filter(({ field }) => field !== "description");
    otherSuggestions.forEach(({ field, value }) =>
      this.applySuggestionToFormik(field, value, formik)
    );

    this.setState({ filledSuggestions: suggestions });
  };

  render() {
    const { suggestions } = this.props;
    const { filledSuggestions } = this.state;

    const isFilled = filledSuggestions === suggestions;

    return (
      <Button
        positive
        fluid
        type="button"
        icon={isFilled ? "check" : "magic"}
        content={
          isFilled
            ? i18next.t("Suggestions applied!")
            : i18next.t("Fill extracted fields")
        }
        labelPosition="left"
        onClick={this.handleClick}
      />
    );
  }
}

const authorShape = PropTypes.shape({
  name: PropTypes.string.isRequired,
  affiliation: PropTypes.string,
  orcid: PropTypes.string,
});

ApplySuggestionButtonComponent.propTypes = {
  suggestions: PropTypes.arrayOf(
    PropTypes.shape({
      field: PropTypes.string.isRequired,
      value: PropTypes.oneOfType([PropTypes.string, PropTypes.arrayOf(authorShape)]),
    })
  ).isRequired,
  formik: PropTypes.object.isRequired,
};

export const ApplySuggestionsButton = connectFormik(ApplySuggestionButtonComponent);
