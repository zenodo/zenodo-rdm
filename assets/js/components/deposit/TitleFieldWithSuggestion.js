import React, { Fragment } from "react";
import PropTypes from "prop-types";
import { TitlesField } from "@js/invenio_rdm_records";
import { FieldSuggestion } from "@js/invenio_app_rdm/deposit/orcha";

export const TitleFieldWithSuggestion = ({ vocabularies, fieldPath, record }) => (
  <Fragment>
    <TitlesField
      options={vocabularies.metadata.titles}
      fieldPath={fieldPath}
      recordUI={record.ui}
      required
    />
    <FieldSuggestion field="title" />
  </Fragment>
);

TitleFieldWithSuggestion.propTypes = {
  vocabularies: PropTypes.object.isRequired,
  fieldPath: PropTypes.string.isRequired,
  record: PropTypes.object.isRequired,
};
