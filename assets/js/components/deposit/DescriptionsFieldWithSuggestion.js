import React, { Fragment } from "react";
import PropTypes from "prop-types";
import { DescriptionsField } from "@js/invenio_rdm_records";
import _get from "lodash/get";
import { FieldSuggestion } from "@js/invenio_app_rdm/deposit/orcha";

export const DescriptionsFieldWithSuggestion = ({
  record,
  vocabularies,
  fieldPath,
}) => (
  <Fragment>
    <DescriptionsField
      fieldPath={fieldPath}
      options={vocabularies.metadata.descriptions}
      recordUI={_get(record, "ui", null)}
    />
    <FieldSuggestion field="description" />
  </Fragment>
);

DescriptionsFieldWithSuggestion.propTypes = {
  record: PropTypes.object.isRequired,
  vocabularies: PropTypes.object.isRequired,
  fieldPath: PropTypes.string.isRequired,
};
