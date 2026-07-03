// SPDX-FileCopyrightText: 2022 CERN
// SPDX-License-Identifier: GPL-3.0-or-later
import { createRoot } from "react-dom/client";
import { CitationsSearch } from "./CitationsSearch";

const citationsContainer = document.getElementById("citations-search");
if (citationsContainer) {
  const recordPIDs = citationsContainer.dataset.recordPids;
  const recordParentPIDs = citationsContainer.dataset.recordParentPids;
  const citationsEndpoint = citationsContainer.dataset.citationsEndpoint;

  createRoot(citationsContainer).render(
    <CitationsSearch
      recordPIDs={JSON.parse(recordPIDs)}
      recordParentPIDs={JSON.parse(recordParentPIDs)}
      endpoint={citationsEndpoint}
    />
  );
}
