// SPDX-FileCopyrightText: 2022 CERN
// SPDX-License-Identifier: GPL-3.0-or-later
import React from "react";
import ReactDOM from "react-dom";
import { CitationsSearch } from "./CitationsSearch";

const citationsContainer = document.getElementById("citations-search");
const recordPIDs = citationsContainer.dataset.recordPids;
const recordParentPIDs = citationsContainer.dataset.recordParentPids;
const citationsEndpoint = citationsContainer.dataset.citationsEndpoint;

citationsContainer &&
  ReactDOM.render(
    <CitationsSearch
      recordPIDs={JSON.parse(recordPIDs)}
      recordParentPIDs={JSON.parse(recordParentPIDs)}
      endpoint={citationsEndpoint}
    />,
    citationsContainer
  );
