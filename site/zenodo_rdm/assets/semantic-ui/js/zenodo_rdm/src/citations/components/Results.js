// SPDX-FileCopyrightText: 2022 CERN
// SPDX-License-Identifier: GPL-3.0-or-later
import React from "react";
import { PropTypes } from "prop-types";
import { sanitizeCitation } from "../sanitizer";
import { withState } from "react-searchkit";
import { Table } from "semantic-ui-react";
import { CitationRow } from "./CitationRow";

export const Results = withState(({ currentResultsState }) => {
  return (
    <Table striped className="citations">
      <Table.Body>
        {currentResultsState?.data.hits.map((result) => {
          return (
            <CitationRow citation={sanitizeCitation(result)} key={result.metadata.ID} />
          );
        })}
      </Table.Body>
    </Table>
  );
});

Results.propTypes = {
  currentResultsState: PropTypes.object,
};

Results.defaultProps = {
  currentResultsState: null,
};
