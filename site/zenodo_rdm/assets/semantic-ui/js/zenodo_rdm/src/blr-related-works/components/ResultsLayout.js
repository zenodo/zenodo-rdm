// SPDX-FileCopyrightText: 2023 CERN
// SPDX-License-Identifier: GPL-3.0-or-later
import React from "react";
import PropTypes from "prop-types";
import { Grid, Item } from "semantic-ui-react";

export const ResultsListLayout = ({ results }) => (
  <Item.Group unstackable divided relaxed link>
    {results}
  </Item.Group>
);

ResultsListLayout.propTypes = {
  results: PropTypes.array.isRequired,
};

export const ResultsGridLayout = ({ results }) => (
  <Grid columns="4" doubling stackable>
    {results}
  </Grid>
);

ResultsGridLayout.propTypes = {
  results: PropTypes.array.isRequired,
};
