// SPDX-FileCopyrightText: 2026 CERN
// SPDX-License-Identifier: GPL-3.0-or-later

import React, { Component } from "react";
import { connect } from "react-redux";
import PropTypes from "prop-types";
import { Message, Icon } from "semantic-ui-react";
import { http, withCancel } from "react-invenio-forms";
import { i18next } from "@translations/invenio_app_rdm/i18next";

export class OrchaWaitlistBannerComponent extends Component {
    constructor(props) {
        super(props);
        this.state = { showBanner: false };
    }

    componentDidMount() {
        this.cancellableFetch = withCancel(http.get("/ai-assist-features-waitlist/status"));
        this.cancellableFetch.promise
            .then((response) => {
                this.setState({ showBanner: Boolean(response.data.show_banner) });
            })
            .catch((error) => {
                if (error !== "UNMOUNTED") {
                    console.log(error);
                }
            });
    }

    componentWillUnmount() {
        if (this.cancellableFetch) {
            this.cancellableFetch.cancel()
        }
    }

    render() {
        const { showBanner } = this.state;
        const { community } = this.props;
        if (!showBanner || ! community) {
            return null;
        }
        return (
            <Message info>
                <Message.Header>
                    Help us test the new AI-assisted deposit form!
                </Message.Header>
                <p>
                    We are looking for 100 users to test new AI-assisted features in the Zenodo deposit form. Help us improve the deposit experience and make metadata entry up to 50% faster.
                </p>
                <a href="/ai-assist-features-waitlist" target="blank">
                    👉 Join the testing and share your feedback!
                </a>.
            </Message>
        )
    }
}

OrchaWaitlistBannerComponent.propTypes = {
    community: PropTypes.object,
};

OrchaWaitlistBannerComponent.defaultProps = {
    community: undefined,
};

const mapStateToProps = (state) => ({
    community: state.deposit.editorState.selectedCommunity,
});

export const OrchaWaitlistBanner = connect(mapStateToProps)(OrchaWaitlistBannerComponent);
