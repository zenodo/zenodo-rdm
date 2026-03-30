// SPDX-FileCopyrightText: 2022 CERN
// SPDX-License-Identifier: GPL-3.0-or-later
import { PropTypes } from "prop-types";
import React from "react";
import { Label } from "semantic-ui-react";

export const Counter = ({ totalResults }) => (
  <Label size="small" circular className="neutral">
    {totalResults}
  </Label>
);

Counter.propTypes = {
  totalResults: PropTypes.string.isRequired,
};
