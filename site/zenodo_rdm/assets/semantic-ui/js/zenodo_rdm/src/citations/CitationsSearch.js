// SPDX-FileCopyrightText: 2022 CERN
// SPDX-License-Identifier: GPL-3.0-or-later
import React from "react";
import { PropTypes } from "prop-types";
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
import { Grid, Accordion, Icon, Label } from "semantic-ui-react";
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
  [`${citationSearchAppID}.BucketAggregationContainer.element`]: ({ valuesCmp }) =>
    valuesCmp,
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

  initialState = (recordParentPID) => {
    return {
      sortBy: "mostrecent",
      sortOrder: "asc",
      layout: "list",
      page: 1,
      size: 10,
      filters: [
        ["group_by", "version"],
        ["id", recordParentPID],
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
    const { recordPIDs, recordParentPIDs } = this.props;
    const recordPID = _get(recordPIDs, "doi.identifier");
    const recordParentPID = _get(recordParentPIDs, "doi.identifier");
    return (
      <OverridableContext.Provider value={overriddenComponents}>
        <ReactSearchKit
          appName={citationSearchAppID}
          searchApi={this.searchApi()}
          initialQueryState={this.initialState(recordParentPID)}
          urlHandlerApi={{ enabled: false }}
        >
          <Accordion className="panel">
            <Accordion.Title
              active={active}
              onClick={this.handleAccordion}
              className="panel-heading"
            >
              Citations
              <a
                href="https://support.zenodo.org/help/en-gb/25-citations"
                target="_blank"
                className="ml-5 mr-5"
                rel="noreferrer"
                aria-label="Citations help page"
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
                    <Filter recordPID={recordPID} recordParentPID={recordParentPID} />
                  </Grid.Column>

                  <Grid.Column width="6">
                    <Label
                      as="label"
                      content="Search citations"
                      htmlFor="citations-search-bar"
                      className="hidden"
                    />
                    <SearchBar
                      uiProps={{
                        name: "citations-search",
                        id: "citations-search-bar",
                      }}
                      placeholder="Search for citation ..."
                    />
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
                    <Pagination options={{ size: "mini", showEllipsis: true }} />
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
  recordParentPIDs: PropTypes.object.isRequired,
  endpoint: PropTypes.string.isRequired,
};
