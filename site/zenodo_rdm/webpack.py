# SPDX-FileCopyrightText: 2019-2026 CERN
# SPDX-FileCopyrightText: 2019-2022 Northwestern University
# SPDX-FileCopyrightText: 2022 TU Wien
# SPDX-FileCopyrightText: 2022 Graz University of Technology
# SPDX-License-Identifier: GPL-3.0-or-later
"""JS/CSS Webpack bundles for theme."""

from invenio_assets.webpack import WebpackThemeBundle

theme = WebpackThemeBundle(
    __name__,
    "assets",
    default="semantic-ui",
    themes={
        "semantic-ui": dict(
            entry={
                # Add your webpack entrypoints
                "zenodo-rdm-support": "./js/zenodo_rdm/src/support/support.js",
                "zenodo-rdm-citations": "./js/zenodo_rdm/src/citations/index.js",
                "zenodo-rdm-communities-carousel": "./js/zenodo_rdm/src/communities-carousel.js",
                "zenodo-rdm-blr-search": "./js/zenodo_rdm/src/blr-related-works/index.js",
                "zenodo-rdm-branded-community-frontpage": "./js/zenodo_rdm/src/branded-community/index.js",
                "zenodo-rdm-orcha-waitlist-banner": "./js/zenodo_rdm/src/orcha-waitlist-banner.js",
                "image-previewer": "./less/zenodo_rdm/previewer/image-previewer.less",
            },
        ),
    },
)
