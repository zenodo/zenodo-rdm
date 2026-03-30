// SPDX-FileCopyrightText: 2022 CERN
// SPDX-License-Identifier: GPL-3.0-or-later
import React from "react";
import { Table, Popup, Icon, Label, Header } from "semantic-ui-react";
import _truncate from "lodash/truncate";
import { PropTypes } from "prop-types";

export const CitationRow = ({ citation }) => {
  const citationInfo = `Citation provided by ${citation.providerNames}`;

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
