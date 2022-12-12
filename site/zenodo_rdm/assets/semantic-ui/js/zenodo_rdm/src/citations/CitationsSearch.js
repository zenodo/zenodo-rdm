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
import _truncate from "lodash/truncate";
import {
  ReactSearchKit,
  InvenioSearchApi,
  ResultsLoader,
  SearchBar,
  Error,
  Pagination,
  ResultsPerPage,
  EmptyResults,
  Count,
} from "react-searchkit";
import { OverridableContext } from "react-overridable";
import { Grid, Accordion, Icon } from "semantic-ui-react";
import _get from "lodash/get";
import { Results } from "./components/Results";
import { Filter } from "./components/Filter";
import { NoCitations } from "./components/NoCitations";
import { ErrorMessage } from "./components/ErrorMessage";
import { Counter } from "./components/Counter";
import { apiConfig } from "./api/config";

const citationSearchAppID = "citationsSearch";

const resultsPerPageValues = [
  { text: "10", value: 10 },
  { text: "20", value: 20 },
  { text: "30", value: 30 },
];

const overriddenComponents = {
  [`${citationSearchAppID}.BucketAggregation.element`]: ({ containerCmp }) =>
    containerCmp,
  [`${citationSearchAppID}.BucketAggregationContainer.element`]: ({
    valuesCmp,
  }) => valuesCmp,
  [`${citationSearchAppID}.EmptyResults.element`]: NoCitations,
  [`${citationSearchAppID}.Error.element`]: ErrorMessage,
  [`${citationSearchAppID}.Count.element`]: Counter,
};

export class CitationsSearch extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      active: true,
    };
  }

  initialState = () => {
    const { recordPIDs } = this.props;
    const doi = _get(recordPIDs, "doi.identifier");
    return {
      sortBy: "mostrecent",
      sortOrder: "asc",
      layout: "list",
      page: 1,
      size: 10,
      filters: [
        ["group_by", "version"],
        ["id", doi],
        ["relation", "isCitedBy"],
        ["scheme", "doi"],
      ],
    };
  };

  searchApi = () => {
    const { endpoint } = this.props;
    const apiConfigObj = apiConfig(endpoint);
    return new InvenioSearchApi(apiConfigObj);
  };

  handleAccordion = () => {
    const { active } = this.state;
    this.setState({ active: !active });
  };

  render() {
    const { active } = this.state;
    return (
      <OverridableContext.Provider value={overriddenComponents}>
        <ReactSearchKit
          appName={citationSearchAppID}
          searchApi={this.searchApi()}
          initialQueryState={this.initialState()}
        >
          <Accordion className="panel">
            <Accordion.Title
              active={active}
              onClick={this.handleAccordion}
              className="panel-heading"
            >
              Citations
              <a
                href="https://help.zenodo.org/#citations"
                target="_blank"
                className="ml-5 mr-5"
              >
                <Icon name="question circle" className="button" />
              </a>
              <Count />
              <Icon name="angle right" />
            </Accordion.Title>

            <Accordion.Content active={active}>
              <Grid padded>
                <Grid.Row>
                  <Grid.Column width="10">
                    <Filter />
                  </Grid.Column>

                  <Grid.Column width="6">
                    <SearchBar placeholder="Search for citation ..." />
                  </Grid.Column>
                </Grid.Row>
              </Grid>

              <Grid className="mt-0">
                <Grid.Row className="pt-0">
                  <Grid.Column>
                    <ResultsLoader>
                      <Results />
                      <Error />
                      <EmptyResults />
                    </ResultsLoader>
                  </Grid.Column>
                </Grid.Row>
              </Grid>

              <Grid padded>
                <Grid.Row>
                  <Grid.Column
                    computer="13"
                    tablet="10"
                    mobile="16"
                    textAlign="center"
                    className="pr-0"
                  >
                    <Pagination
                      options={{ size: "mini", showEllipsis: true }}
                    />
                  </Grid.Column>

                  <Grid.Column
                    computer="3"
                    tablet="6"
                    mobile="16"
                    textAlign="right"
                    className="pl-0"
                  >
                    <ResultsPerPage
                      values={resultsPerPageValues}
                      label={(cmp) => <>Page size: {cmp}</>}
                    />
                  </Grid.Column>
                </Grid.Row>
              </Grid>
            </Accordion.Content>
          </Accordion>
        </ReactSearchKit>
      </OverridableContext.Provider>
    );
  }
}

CitationsSearch.propTypes = {
  recordPIDs: PropTypes.object.isRequired,
};
