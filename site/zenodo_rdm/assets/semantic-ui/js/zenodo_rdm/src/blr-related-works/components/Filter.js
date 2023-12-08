// This file is part of Zenodo.
// Copyright (C) 2023 CERN.
//
// Zenodo is free software; you can redistribute it
// and/or modify it under the terms of the GNU General Public License as
// published by the Free Software Foundation; either version 2 of the
// License, or (at your option) any later version.
//
// Zenodo is distributed in the hope that it will be
// useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
// General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with Zenodo; if not, write to the
// Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
// MA 02111-1307, USA.
//
// In applying this license, CERN does not
// waive the privileges and immunities granted to it by virtue of its status
// as an Intergovernmental Organization or submit itself to any jurisdiction.

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
