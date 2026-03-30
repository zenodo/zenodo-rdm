// SPDX-FileCopyrightText: 2023 CERN
// SPDX-License-Identifier: GPL-3.0-or-later
export const apiConfig = (endpoint) => ({
  axios: {
    url: endpoint,
    timeout: 5000,
    headers: {
      Accept: "application/vnd.inveniordm.v1+json",
    },
  },
});
