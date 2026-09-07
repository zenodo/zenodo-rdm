// SPDX-FileCopyrightText: 2026 CERN
// SPDX-License-Identifier: GPL-3.0-or-later

import React, { Component } from "react";
import { Button, Message } from "semantic-ui-react";
import { http } from "react-invenio-forms";
import { i18next } from "@translations/invenio_app_rdm/i18next";

// Rendered server-side in zenodo_rdm/records/deposit.html
const isBannerEnabled = () => {
  const config = document.getElementById("orcha-waitlist-banner-config");
  return config?.dataset.show === "true";
};

export class OrchaWaitlistBanner extends Component {
  constructor(props) {
    super(props);
    this.state = { showBanner: isBannerEnabled() };
  }

  handleDismiss = () => {
    this.setState({ showBanner: false });
    http.post("/ai-assist-features-waitlist/dismiss").catch((error) => {
      console.error(error);
    });
  };

  render() {
    const { showBanner } = this.state;
    if (!showBanner) {
      return null;
    }
    return (
      <Message info>
        <Message.Header>Help us test the new AI-assisted deposit form!</Message.Header>
        <p>
          We are looking for users to test new AI-assisted features in the Zenodo
          deposit form. Help us improve the deposit experience and speed up metadata
          entry.
        </p>
        <a href="/ai-assist-features-waitlist" target="_blank">
          👉 Join as a tester and share your feedback!
        </a>
        <div className="rel-mt-1">
          <Button type="button" basic size="mini" onClick={this.handleDismiss}>
            {i18next.t("Don't show again")}
          </Button>
        </div>
      </Message>
    );
  }
}
