import React from "react";
import { Header, Grid } from "semantic-ui-react";
import { makeIdEntry, makeSubheader } from "react-invenio-forms";


export const CustomAffiliationsSuggestions = (creatibutors) => {
  // Ensure creatibutors is always an array
  const creatibutorsArray = Array.isArray(creatibutors) ? creatibutors : [creatibutors];

  return creatibutorsArray.map((creatibutor) => {
    const { creatibutor: creatibutorData } = creatibutor;
    const { name, acronym, identifiers = [], id } = creatibutorData;

    const subheader = makeSubheader(creatibutorData, creatibutor.isOrganization);
    const displayName = acronym ? `${name} (${acronym})` : name;

    const sources = [];
    const idStrings = [];

    identifiers.forEach((identifier) => {
      const { scheme, identifier: value } = identifier;

      if (scheme === "ror") {
        sources.push(
          <span key={value}>
            Source: {scheme.toUpperCase()} <span>(Preferred)</span>
          </span>
        );
      } else if (scheme === "edmo") {
        sources.push(
          <span key={value}>Source: {scheme.toUpperCase()}</span>
        );
      } else {
        const idEntry = makeIdEntry(identifier);
        if (idEntry) idStrings.push(idEntry);
      }
    });

    return (
      <Grid key={id}>
        <Grid.Row columns={2} verticalAlign="middle">
          <Grid.Column width={12}>
            <Header>
              {displayName} {idStrings.length > 0 && <>({idStrings})</>}
              {subheader && <Header.Subheader>{subheader}</Header.Subheader>}
            </Header>
          </Grid.Column>
          <Grid.Column width={4} textAlign="right">
            {sources.length > 0 && (
              <Header as="h6" color="grey" style={{ margin: 0 }}>
                {sources}
              </Header>
            )}
          </Grid.Column>
        </Grid.Row>
      </Grid>
    );
  });
};
