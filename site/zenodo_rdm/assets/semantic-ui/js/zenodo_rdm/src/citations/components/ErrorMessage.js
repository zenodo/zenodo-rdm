// SPDX-FileCopyrightText: 2022 CERN
// SPDX-License-Identifier: GPL-3.0-or-later
import React from "react";
import { Message } from "semantic-ui-react";

export const ErrorMessage = () => (
  <Message error as="p" className="rel-ml-1 rel-mr-1">
    Oops! Something went wrong while fetching results.
  </Message>
);
