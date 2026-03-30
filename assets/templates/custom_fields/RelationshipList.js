// SPDX-FileCopyrightText: 2025 CERN
// SPDX-License-Identifier: GPL-3.0-or-later
import React, { Component } from "react";
import PropTypes from "prop-types";
import { Button, Form, Icon, Dropdown } from "semantic-ui-react";
import {
  ArrayField,
  GroupField,
  showHideOverridableWithDynamicId,
} from "react-invenio-forms";

const emptyRelationship = { subject: [], object: [] };

/**
 * A multi-value tag input using Semantic UI Dropdown.
 */
class TagInput extends Component {
  handleChange = (e, { value }) => {
    this.props.onChange(value);
  };

  render() {
    const { value, placeholder } = this.props;
    const options = (value || []).map((v) => ({ key: v, text: v, value: v }));

    return (
      <Dropdown
        fluid
        multiple
        search
        selection
        allowAdditions
        additionLabel="Add "
        placeholder={placeholder}
        value={value || []}
        options={options}
        onChange={this.handleChange}
        noResultsMessage="Type to add..."
      />
    );
  }
}

TagInput.propTypes = {
  value: PropTypes.array,
  placeholder: PropTypes.string,
  onChange: PropTypes.func.isRequired,
};

TagInput.defaultProps = {
  value: [],
  placeholder: "",
};

/**
 * Main component for editing a list of biotic relationships.
 * Used for the obo:RO_0002453 (Host of) custom field.
 */
class RelationshipListComponent extends Component {
  render() {
    const { fieldPath, label, labelIcon, helpText, subject, object } = this.props;

    return (
      <>
        {label && (
          <label className="field-label-class invenio-field-label" htmlFor={fieldPath}>
            <strong>{label}</strong>
          </label>
        )}

        <ArrayField
          addButtonLabel="Add relationship"
          defaultNewValue={emptyRelationship}
          fieldPath={fieldPath}
          helpText={helpText}
        >
          {({ arrayHelpers, indexPath, array }) => {
            const relationship = array[indexPath] || emptyRelationship;

            const handleSubjectChange = (newValue) => {
              arrayHelpers.replace(indexPath, { ...relationship, subject: newValue });
            };

            const handleObjectChange = (newValue) => {
              arrayHelpers.replace(indexPath, { ...relationship, object: newValue });
            };

            return (
              <GroupField>
                <Form.Field width={7}>
                  <strong style={{ display: "block", marginBottom: "0.5em" }}>
                    {subject?.label || "Subject"}
                  </strong>
                  <TagInput
                    value={relationship.subject}
                    placeholder={subject?.placeholder || ""}
                    onChange={handleSubjectChange}
                  />
                </Form.Field>

                <Form.Field width={1} style={{ display: "flex", alignItems: "flex-end", justifyContent: "center", paddingBottom: "0.85em" }}>
                  <Icon name="arrow right" />
                </Form.Field>

                <Form.Field width={7}>
                  <strong style={{ display: "block", marginBottom: "0.5em" }}>
                    {object?.label || "Object"}
                  </strong>
                  <TagInput
                    value={relationship.object}
                    placeholder={object?.placeholder || ""}
                    onChange={handleObjectChange}
                  />
                </Form.Field>

                <Form.Field width={1} style={{ display: "flex", alignItems: "flex-end", paddingBottom: "0.6em" }}>
                  <Button
                    aria-label="Remove field"
                    className="close-btn"
                    icon="close"
                    onClick={() => arrayHelpers.remove(indexPath)}
                  />
                </Form.Field>
              </GroupField>
            );
          }}
        </ArrayField>
      </>
    );
  }
}

RelationshipListComponent.propTypes = {
  fieldPath: PropTypes.string.isRequired,
  label: PropTypes.oneOfType([PropTypes.string, PropTypes.node]),
  labelIcon: PropTypes.string,
  helpText: PropTypes.string,
  subject: PropTypes.shape({
    label: PropTypes.string,
    placeholder: PropTypes.string,
  }),
  object: PropTypes.shape({
    label: PropTypes.string,
    placeholder: PropTypes.string,
  }),
};

RelationshipListComponent.defaultProps = {
  label: undefined,
  labelIcon: undefined,
  helpText: undefined,
  subject: {},
  object: {},
};

export const RelationshipList = showHideOverridableWithDynamicId(RelationshipListComponent);
