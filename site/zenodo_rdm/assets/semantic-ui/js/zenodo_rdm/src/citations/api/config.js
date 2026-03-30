// SPDX-FileCopyrightText: 2022 CERN
// SPDX-License-Identifier: GPL-3.0-or-later
export const apiConfig = (endpoint) => ({
  axios: {
    url: endpoint,
    timeout: 5000,
    headers: {
      Accept: "application/json",
    },
  },
});
