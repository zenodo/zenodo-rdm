// SPDX-FileCopyrightText: 2023 CERN
// SPDX-License-Identifier: GPL-3.0-or-later
import React from "react";
import { Container } from "semantic-ui-react";

export const NoResults = () => {
  return (
    <Container align="left">
      <p>
        <em>No related content for this record</em>
      </p>
    </Container>
  );
};
