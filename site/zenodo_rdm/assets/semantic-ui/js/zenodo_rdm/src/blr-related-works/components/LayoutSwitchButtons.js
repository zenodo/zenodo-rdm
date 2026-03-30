// SPDX-FileCopyrightText: 2023 CERN
// SPDX-License-Identifier: GPL-3.0-or-later
import React from "react";
import { PropTypes } from "prop-types";
import { Button } from "semantic-ui-react";
import { withState } from "react-searchkit";

export const LayoutSwitchButtons = withState(
  ({ updateQueryState, currentQueryState, currentLayout, onLayoutChange }) => {
    const handleLayoutChange = (layout) => {
      const numOfRecords = layout === "grid" ? 12 : 6;
      updateQueryState({ ...currentQueryState, size: numOfRecords });
      onLayoutChange(layout);
    };

    return (
      <Button.Group>
        <Button
          icon="th"
          name="grid"
          active={currentLayout === "grid"}
          onClick={() => handleLayoutChange("grid")}
          aria-label="Grid view"
        />
        <Button
          icon="th list"
          name="list"
          active={currentLayout === "list"}
          onClick={() => handleLayoutChange("list")}
          aria-label="List view"
        />
      </Button.Group>
    );
  }
);

LayoutSwitchButtons.propTypes = {
  currentLayout: PropTypes.string.isRequired,
  onLayoutChange: PropTypes.func.isRequired,
  updateQueryState: PropTypes.func.isRequired,
  currentQueryState: PropTypes.object.isRequired,
};
