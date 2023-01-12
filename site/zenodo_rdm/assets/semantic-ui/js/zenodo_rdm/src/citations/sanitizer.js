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
import _get from "lodash/get";

function providerNamesFilter(relationship) {
  const history = _get(relationship, "metadata.History");

  let providerNames = [];

  history.forEach((linkHistory) => {
    const linkProvider = _get(linkHistory, "LinkProvider");

    linkProvider.forEach((provider) => {
      if (!providerNames.includes(provider.Name)) {
        providerNames.push(provider.Name);
      }
    });
  });
  return providerNames.join(", ");
}

function creatorNamesFilter(relationship) {
  const creators = _get(relationship, "metadata.Source.Creator");

  let creatorNames = "";

  if (creators) {
    creatorNames = creators[0].Name;
    if (creators.length === 2) {
      creatorNames = `${creatorNames} & ${creators[1].Name}`;
    } else if (creators.length > 2) {
      creatorNames = `${creatorNames} et al.`;
    }
  }
  return creatorNames;
}

function doiUrlFilter(relationship) {
  const identifiers = _get(relationship, "metadata.Source.Identifier");

  let doiUrl = null;
  let url = null;

  identifiers &&
    identifiers.forEach((identifier) => {
      if (identifier.IDURL) {
        url = identifier.IDURL;
        if (identifier.IDScheme === "doi") {
          doiUrl = identifier.IDURL;
        }
      }
    });

  return doiUrl || url;
}

function doiFilter(relationship) {
  const identifiers = _get(relationship, "metadata.Source.Identifier");

  let doi = null;

  identifiers &&
    identifiers.forEach((identifier) => {
      if (identifier.ID && identifier.IDScheme === "doi") {
        doi = identifier.ID;
      }
    });

  return doi;
}

function citationTitleFilter(relationship) {
  const identifiers = _get(relationship, "metadata.Source.Identifier");

  let title = _get(relationship, "metadata.Source.Title");

  if (!title || title.length === 0) {
    // Use the first identifier or the DOI
    identifiers &&
      identifiers.forEach((identifier) => {
        if (identifier.IDURL) {
          title = `${identifier.IDScheme.toUpperCase()}: ${identifier.ID}`;

          if (identifier.IDScheme === "doi") {
            title = `DOI: ${identifier.ID}`;
          }
        }
      });
  }
  return title;
}

function iconTypeFilter(relationship) {
  const typeName = _get(relationship, "metadata.Source.Type.Name");

  const iconType = {
    literature: "file alternate",
    dataset: "table",
    software: "code",
    unknown: "asterisk",
  };

  return iconType[typeName] || iconType["unknown"];
}

function uniqueBadgeFilter(relationship) {
  const identifiers = _get(relationship, "metadata.Source.Identifier");

  let schemes = [];
  let uniqueIdentifiers = [];

  identifiers &&
    identifiers.forEach((identifier) => {
      if (identifier.IDURL && !schemes.includes(identifier.IDScheme)) {
        uniqueIdentifiers.push(identifier);
        schemes.push(identifier.IDScheme);
      }
    });
  return uniqueIdentifiers;
}

function missingTypesFilter(buckets) {
  let missingTypes = ["literature", "dataset", "software", "unknown"];

  buckets &&
    buckets.forEach((bucket) => {
      missingTypes.splice(missingTypes.indexOf(bucket.key), 1);
    });

  return missingTypes;
}

function dateSanitizer(relationship) {
  const date = new Date(relationship.metadata.Source.PublicationDate);
  return !isNaN(date.getFullYear()) && date.getFullYear();
}

function sanitizeCitation(relationship) {
  return {
    badges: uniqueBadgeFilter(relationship),
    title: citationTitleFilter(relationship),
    creatorNames: creatorNamesFilter(relationship),
    providerNames: providerNamesFilter(relationship),
    doiUrl: doiUrlFilter(relationship),
    doi: doiFilter(relationship),
    icon: iconTypeFilter(relationship),
    publicationYear: dateSanitizer(relationship),
  };
}

export { missingTypesFilter, sanitizeCitation };
