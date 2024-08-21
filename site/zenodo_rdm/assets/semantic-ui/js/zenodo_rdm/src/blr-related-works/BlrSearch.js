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
import PropTypes from "prop-types";
import {
  ReactSearchKit,
  InvenioSearchApi,
  ResultsLoader,
  ResultsMultiLayout,
  Error,
  EmptyResults,
  Pagination,
  BucketAggregation,
  LayoutSwitcher,
} from "react-searchkit";
import { OverridableContext } from "react-overridable";
import { apiConfig } from "./api/config";
import { Segment, Container } from "semantic-ui-react";
import { ResultsGridLayout, ResultsListLayout } from "./components/ResultsLayout";
import { RecordGridItem, RecordListItem } from "./components/RecordItem";
import { FilterContainer, Filter, FilterValues } from "./components/Filter";
import { LayoutSwitchButtons } from "./components/LayoutSwitchButtons";
import { NoResults } from "./components/NoResults";
import { BlrResultsLoader } from "./components/BlrResultsLoader";

const blrSearchAppID = "blrSearch";

const overriddenComponents = {
  [`${blrSearchAppID}.ResultsGrid.container`]: ResultsGridLayout,
  [`${blrSearchAppID}.ResultsGrid.item`]: RecordGridItem,
  [`${blrSearchAppID}.ResultsList.container`]: ResultsListLayout,
  [`${blrSearchAppID}.ResultsList.item`]: RecordListItem,
  [`${blrSearchAppID}.BucketAggregation.element`]: FilterContainer,
  [`${blrSearchAppID}.BucketAggregationContainer.element`]: Filter,
  [`${blrSearchAppID}.BucketAggregationValues.element`]: FilterValues,
  [`${blrSearchAppID}.LayoutSwitcher.element`]: LayoutSwitchButtons,
  [`${blrSearchAppID}.EmptyResults.element`]: NoResults,
  [`${blrSearchAppID}.ResultsLoader.element`]: BlrResultsLoader,
};

export const BlrSearch = ({ endpoint, recordDOI, resourceType, blrId }) => {
  const relationType = (resourceType) =>
    resourceType === "Journal article" || resourceType === "Book chapter"
      ? "ispartof"
      : "haspart";

  const queryString = (relationType, identifier) =>
    `parent.communities.ids:${blrId} AND metadata.related_identifiers.relation_type.id:${relationType} AND metadata.related_identifiers.identifier:"${identifier}"`;

  const searchApi = new InvenioSearchApi(apiConfig(endpoint));

  const initialState = {
    queryString: queryString(relationType(resourceType), recordDOI),
    sortBy: "bestmatch",
    sortOrder: "asc",
    page: 1,
    size: 12,
    layout: "grid",
  };

  return (
    <OverridableContext.Provider value={overriddenComponents}>
      <ReactSearchKit
        appName={blrSearchAppID}
        searchApi={searchApi}
        urlHandlerApi={{ enabled: false }}
        initialQueryState={initialState}
      >
        <>
          <div className="flex align-items-center justify-space-between">
            <BucketAggregation
              agg={{ field: "resource_type", aggName: "resource_type" }}
            />
            <LayoutSwitcher />
          </div>

          <Segment>
            <ResultsLoader>
              <ResultsMultiLayout />
              <Error />
              <EmptyResults />
              <Container align="center" className="rel-pt-1">
                <Pagination options={{ size: "mini", showEllipsis: true }} />
              </Container>
            </ResultsLoader>
          </Segment>
        </>
      </ReactSearchKit>
    </OverridableContext.Provider>
  );
};

BlrSearch.propTypes = {
  endpoint: PropTypes.string.isRequired,
  recordDOI: PropTypes.string.isRequired,
  resourceType: PropTypes.string.isRequired,
  blrId: PropTypes.string.isRequired,
};
