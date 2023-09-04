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
import { Table, Popup, Icon, Label, Header } from "semantic-ui-react";
import _truncate from "lodash/truncate";
import { PropTypes } from "prop-types";

export const CitationRow = ({ citation }) => {
  const citationInfo = `Citation procided by ${citation.providerNames}`;

  return (
    <Table.Row>
      <Table.Cell>
        <Icon name={citation.icon} size="large" />
      </Table.Cell>

      <Table.Cell>
        <Header size="tiny">
          <a href={citation.doiUrl} target="_blank" rel="noreferrer">
            {_truncate(citation.title, { length: 80 })}
          </a>
          <Header.Subheader className="mt-5">
            {citation.creatorNames} {citation.doi && `(DOI: ${citation.doi})`}
          </Header.Subheader>
        </Header>
      </Table.Cell>

      <Table.Cell>{citation.publicationYear}</Table.Cell>
      <Table.Cell collapsing>
        {citation.badges?.map((identifier) => (
          <Popup
            inverted
            size="mini"
            content={identifier.ID}
            key={identifier.ID}
            trigger={
              <a
                href={identifier.IDURL}
                target="_blank"
                aria-label={`${identifier.IDScheme}: ${identifier.ID}`}
                rel="noreferrer"
              >
                <Label size="tiny" className="primary uppercase mr-5">
                  {identifier.IDScheme}
                </Label>
              </a>
            }
          />
        ))}
      </Table.Cell>

      <Table.Cell collapsing>
        <Popup
          inverted
          size="mini"
          content={citationInfo}
          trigger={
            <Icon role="note" name="question circle" aria-label={citationInfo} />
          }
        />
      </Table.Cell>
    </Table.Row>
  );
};

CitationRow.propTypes = {
  citation: PropTypes.object.isRequired,
};
