import React from "react";
import { Placeholder } from "semantic-ui-react";

export const BlrResultsLoader = (children, loading) => {
  return loading ? (
    <Placeholder fluid>
      <Placeholder.Header image>
        <Placeholder.Line length="long" />
        <Placeholder.Line />
      </Placeholder.Header>
      <Placeholder.Header image>
        <Placeholder.Line length="long" />
        <Placeholder.Line />
      </Placeholder.Header>
    </Placeholder>
  ) : (
    children
  );
};
