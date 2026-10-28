// SPDX-FileCopyrightText: 2026 CERN
// SPDX-License-Identifier: GPL-3.0-or-later

import { http } from "react-invenio-forms";

// Rendered server-side in zenodo_rdm/macros/orcha_waitlist_banner.html
const banner = document.getElementById("orcha-waitlist-banner");
const dismissButton = banner?.querySelector("[data-dismiss-url]");

dismissButton?.addEventListener("click", () => {
  banner.hidden = true;
  http.post(dismissButton.dataset.dismissUrl).catch((error) => {
    console.error(error);
  });
});
