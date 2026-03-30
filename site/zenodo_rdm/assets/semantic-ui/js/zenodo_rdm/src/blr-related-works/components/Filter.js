// SPDX-FileCopyrightText: 2023 CERN
// SPDX-License-Identifier: GPL-3.0-or-later
import React from "react";
import { PropTypes } from "prop-types";
import { Dropdown, Label, Button, Icon } from "semantic-ui-react";
import { withState } from "react-searchkit";

export const FilterContainer = ({ agg, containerCmp, updateQueryFilters }) => {
  const clearFacets = () => {
    if (containerCmp.props.selectedFilters.length) {
      updateQueryFilters([agg.aggName, ""], containerCmp.props.selectedFilters);
    }
  };

  return (
    <div className="flex align-items-center">
      <div>{containerCmp}</div>
      <div>
        <Button onClick={clearFacets} content="Reset filters" />
      </div>
    </div>
  );
};

FilterContainer.propTypes = {
  agg: PropTypes.object.isRequired,
  updateQueryFilters: PropTypes.func.isRequired,
  containerCmp: PropTypes.node.isRequired,
};

export const Filter = withState(({ currentQueryState, valuesCmp }) => {
  const numSelectedFilters = currentQueryState.filters.length;
  return (
    <Dropdown
      text={`Filter by type ${numSelectedFilters ? `(${numSelectedFilters})` : ""}`}
      button
    >
      <Dropdown.Menu>{valuesCmp}</Dropdown.Menu>
    </Dropdown>
  );
});

Filter.propTypes = {
  valuesCmp: PropTypes.array.isRequired,
};

export const FilterValues = ({ bucket, isSelected, onFilterClicked, label }) => {
  return (
    <Dropdown.Item
      key={bucket.key}
      id={`${bucket.key}-agg-value`}
      selected={isSelected}
      onClick={() => onFilterClicked(bucket.key)}
      value={bucket.key}
      className="flex align-items-center justify-space-between"
    >
      {isSelected && <Icon name="check" className="positive" />}

      <span>{label}</span>
      <Label size="small" className="rel-ml-1 mr-0">
        {bucket.doc_count.toLocaleString("en-US")}
      </Label>
    </Dropdown.Item>
  );
};

FilterValues.propTypes = {
  bucket: PropTypes.object.isRequired,
  isSelected: PropTypes.bool.isRequired,
  onFilterClicked: PropTypes.func.isRequired,
  label: PropTypes.string.isRequired,
};
