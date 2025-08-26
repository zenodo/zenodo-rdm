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
import { Grid, Header, Item, Label, Icon } from "semantic-ui-react";
import _get from "lodash/get";
import { SearchItemCreators } from "@js/invenio_app_rdm/utils";
import { Image } from "react-invenio-forms";

const layoutProps = (result) => ({
  accessStatusId: _get(result, "ui.access_status.id", "open"),
  accessStatus: _get(result, "ui.access_status.title_l10n", "Open"),
  accessStatusIcon: _get(result, "ui.access_status.icon", "unlock"),
  createdDate: _get(result, "ui.created_date_l10n_long", "Unknown date"),
  creators: _get(result, "ui.creators.creators", []).slice(0, 3),
  resourceType: _get(result, "ui.resource_type.title_l10n", "No resource type"),
  title: _get(result, "metadata.title", "No title"),
  link: _get(result, "links.self_html", "#"),
  typeIcon: result.ui?.resource_type?.id.includes("image") ? "image" : "file alternate",
});

export const RecordGridItem = ({ result }) => {
  const { title, creators, resourceType, typeIcon, link } = layoutProps(result);
  const thumbnailUrl = result.links.self.thumbnails?.["250"];

  return (
    <Grid.Column className="flex column">
      <Image src={thumbnailUrl} className="thumbnail-image mb-10" loadFallbackFirst />
      <div>
        <div className="pb-10">
          <Label horizontal size="small">
            <Icon name={typeIcon} />
            {resourceType}
          </Label>
        </div>

        <Header href={link} className="ui small header truncate-lines-2 m-0">
          {title}
        </Header>

        <SearchItemCreators creators={creators} />
      </div>
    </Grid.Column>
  );
};

RecordGridItem.propTypes = {
  result: PropTypes.object.isRequired,
};

export const RecordListItem = ({ result }) => {
  const {
    accessStatusId,
    accessStatus,
    accessStatusIcon,
    createdDate,
    creators,
    resourceType,
    title,
    typeIcon,
    link,
  } = layoutProps(result);
  const thumbnailUrl = result.links.self.thumbnails?.["250"];

  return (
    <Item>
      <Image
        size="tiny"
        src={thumbnailUrl}
        className="thumbnail-image"
        loadFallbackFirst
      />

      <Item.Content>
        <div className="pb-10">
          <Label horizontal size="small">
            <Icon name={typeIcon} />
            {resourceType}
          </Label>

          <Label horizontal size="small" className="primary">
            <Icon name="calendar alternate" />
            {createdDate}
          </Label>

          <Label horizontal size="small" className={`access-status ${accessStatusId}`}>
            {accessStatusIcon && <Icon name={accessStatusIcon} />}
            {accessStatus}
          </Label>
        </div>

        <Item.Header href={link} className="ui small header">
          {title}
        </Item.Header>

        <Item.Extra>
          <SearchItemCreators creators={creators} />
        </Item.Extra>
      </Item.Content>
    </Item>
  );
};

RecordListItem.propTypes = {
  result: PropTypes.object.isRequired,
};
