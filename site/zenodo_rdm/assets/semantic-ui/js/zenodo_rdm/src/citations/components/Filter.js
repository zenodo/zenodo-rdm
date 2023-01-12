// This file is part of Zenodo.
// Copyright (C) 2022 CERN.
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
import { missingTypesFilter } from "../sanitizer";
import { withState, BucketAggregation } from "react-searchkit";
import { Grid, Header, List, Checkbox } from "semantic-ui-react";

export const Filter = withState(
  ({ currentResultsState, updateQueryState, currentQueryState }) => {
    const missingTypes = missingTypesFilter(
      currentResultsState.data.aggregations?.type?.buckets
    );

    const toggleGroupBy = (event, data) => {
      const isChecked = data.checked;
      const groupByKey = "group_by";
      const groupByValue = isChecked ? "identity" : "version";

      const filters = currentQueryState.filters.map((filter) => {
        if (filter[0] === groupByKey) return [groupByKey, groupByValue];
        return filter;
      });
      updateQueryState({ ...currentQueryState, filters });
    };

    return (
      <Grid>
        <Grid.Column mobile="16" tablet="4" computer="3">
          <Header size="tiny">
            <b>Show only:</b>
          </Header>
        </Grid.Column>
        <Grid.Column mobile="16" tablet="12" computer="13">
          <List horizontal className="filter-list">
            <BucketAggregation agg={{ field: "type", aggName: "type" }} />

            {missingTypes.map((type) => (
              <List.Item key={type}>
                <Checkbox label={`${type} (0)`} disabled />
              </List.Item>
            ))}

            <List.Item>
              <Checkbox label="Citations to this version" onChange={toggleGroupBy} />
            </List.Item>
          </List>
        </Grid.Column>
      </Grid>
    );
  }
);

Filter.propTypes = {
  currentResultsState: PropTypes.object,
  updateQueryState: PropTypes.func,
  currentQueryState: PropTypes.object,
};

Filter.defaultProps = {
  currentResultsState: null,
  updateQueryState: null,
  currentQueryState: null,
};
