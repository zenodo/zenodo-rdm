// SPDX-FileCopyrightText: 2026 CERN
// SPDX-License-Identifier: GPL-3.0-or-later

import React from "react";
import PropTypes from "prop-types";
import { Icon } from "semantic-ui-react";
import { InvenioPopup } from "react-invenio-forms";

const ORIGIN_ICONS = {
  orcha: "fire blue",
};

/**
 * Form feedback popup; display a specific icon to indicate error comes from an AI check.
 */
export const FeedbackLabelPopup = ({ fieldPath, error, icon }) => (
  <InvenioPopup
    popupId={`invenio-form-feedback-error-${fieldPath}`}
    ariaLabel="Form field feedback error"
    trigger={<Icon name={ORIGIN_ICONS[error.origin] || icon} />}
    // Rule descriptions can contain HTML to link to a page with more details about the rule.
    // This field is sanitized in the backend with SanitizedHTML.
    content={<span dangerouslySetInnerHTML={{ __html: error.description }} />}
    position="top center"
    hoverable
  />
);
