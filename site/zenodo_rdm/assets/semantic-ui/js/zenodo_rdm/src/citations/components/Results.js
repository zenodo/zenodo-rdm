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
