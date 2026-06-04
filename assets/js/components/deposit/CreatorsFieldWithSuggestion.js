import React, { Fragment } from "react";
import PropTypes from "prop-types";
import { CreatibutorsField } from "@js/invenio_rdm_records";
import { i18next } from "@translations/invenio_app_rdm/i18next";
import { FieldSuggestion } from "@js/invenio_app_rdm/deposit/orcha";

export const CreatorsFieldWithSuggestion = ({ vocabularies, config, fieldPath }) => (
  <Fragment>
    <CreatibutorsField
      label={i18next.t("Authors/Creators")}
      labelIcon="user"
      addButtonHelpText={i18next.t(
        "Use the Authors/Creators field for names that should appear in the citation. Use the Contributors field below for other names."
      )}
      fieldPath={fieldPath}
      roleOptions={vocabularies.metadata.creators.role}
      schema="creators"
      autocompleteNames={config.autocomplete_names}
      required
    />
    <FieldSuggestion field="creators" />
  </Fragment>
);

CreatorsFieldWithSuggestion.propTypes = {
  vocabularies: PropTypes.object.isRequired,
  config: PropTypes.object.isRequired,
  fieldPath: PropTypes.string.isRequired,
};
