// SPDX-FileCopyrightText: 2026 CERN.
// SPDX-License-Identifier: GPL-3.0-or-later

import { PropTypes } from "prop-types";
import { useEffect, useRef } from "react";
import { useFormikContext } from "formik";

/**
 * ALTCHA proof-of-work widget (the web component is registered by the
 * ``invenio-accounts-altcha`` bundle). The solution is stored in the ``altcha``
 * Formik field and sent along with the other values.
 */
export default function AltchaField({ challenge }) {
  const ref = useRef(null);
  const { setFieldValue, errors } = useFormikContext();

  useEffect(() => {
    const widget = ref.current;
    if (!widget) return undefined;
    const onStateChange = (ev) => {
      const { state, payload } = ev.detail || {};
      setFieldValue("altcha", state === "verified" && payload ? payload : "");
    };
    widget.addEventListener("statechange", onStateChange);
    return () => widget.removeEventListener("statechange", onStateChange);
  }, [setFieldValue]);

  return (
    <div className={`field flex${errors.altcha ? " error" : ""}`}>
      <altcha-widget ref={ref} challenge={challenge} auto="onfocus" />
      {errors.altcha && (
        <div className="ui pointing red basic label">{errors.altcha}</div>
      )}
    </div>
  );
}

AltchaField.propTypes = {
  challenge: PropTypes.string.isRequired,
};
