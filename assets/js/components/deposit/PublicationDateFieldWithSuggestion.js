import React, { Fragment } from "react";
import PropTypes from "prop-types";
import { PublicationDateField } from "@js/invenio_rdm_records";
import { FieldSuggestion } from "@js/invenio_app_rdm/deposit/orcha";

export const PublicationDateFieldWithSuggestion = ({ fieldPath }) => (
  <Fragment>
    <PublicationDateField required fieldPath={fieldPath} />
    <FieldSuggestion field="publication_date" />
  </Fragment>
);

PublicationDateFieldWithSuggestion.propTypes = {
  fieldPath: PropTypes.string.isRequired,
};
