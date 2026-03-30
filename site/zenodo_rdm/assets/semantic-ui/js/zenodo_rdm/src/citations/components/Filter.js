// SPDX-FileCopyrightText: 2022 CERN
// SPDX-License-Identifier: GPL-3.0-or-later
import React from "react";
import { PropTypes } from "prop-types";
import { missingTypesFilter } from "../sanitizer";
import { withState, BucketAggregation } from "react-searchkit";
import { Grid, Header, List, Checkbox } from "semantic-ui-react";

export const Filter = withState(
  ({
    currentResultsState,
    updateQueryState,
    currentQueryState,
    recordPID,
    recordParentPID,
  }) => {
    const missingTypes = missingTypesFilter(
      currentResultsState.data.aggregations?.type?.buckets
    );

    const toggleGroupBy = (event, data) => {
      const isChecked = data.checked;
      const groupByKey = "group_by";
      const groupByValue = isChecked ? "identity" : "version";
      const idKey = "id";
      const idValue = isChecked ? recordPID : recordParentPID;

      const filters = currentQueryState.filters.map((filter) => {
        if (filter[0] === groupByKey) return [groupByKey, groupByValue];
        if (filter[0] === idKey) return [idKey, idValue];
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
                <Checkbox
                  label={`${type} (0)`}
                  disabled
                  id={`${type}-facet-checkbox`}
                />
              </List.Item>
            ))}

            <List.Item>
              <Checkbox
                label="Citations to this version"
                onChange={toggleGroupBy}
                id="citations-to-version"
              />
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
  recordPID: PropTypes.object.isRequired,
  recordParentPID: PropTypes.object.isRequired,
};

Filter.defaultProps = {
  currentResultsState: null,
  updateQueryState: null,
  currentQueryState: null,
};
