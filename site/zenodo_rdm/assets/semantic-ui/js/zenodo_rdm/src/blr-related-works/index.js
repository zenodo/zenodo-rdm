// SPDX-FileCopyrightText: 2023 CERN
// SPDX-License-Identifier: GPL-3.0-or-later
import React from "react";
import ReactDOM from "react-dom";
import { BlrSearch } from "./BlrSearch";

const blrContainer = document.getElementById("blr-search");
const endpoint = blrContainer.dataset.blrEndpoint;
const recordDOI = JSON.parse(blrContainer.dataset.recordDoi);
const resourceType = JSON.parse(blrContainer.dataset.resourceType);
const blrId = JSON.parse(blrContainer.dataset.blrId);

blrContainer &&
  ReactDOM.render(
    <BlrSearch
      endpoint={endpoint}
      recordDOI={recordDOI}
      resourceType={resourceType}
      blrId={blrId}
    />,
    blrContainer
  );
