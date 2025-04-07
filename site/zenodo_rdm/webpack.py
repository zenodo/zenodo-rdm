# -*- coding: utf-8 -*-
#
# Copyright (C) 2019-2022 CERN.
# Copyright (C) 2019-2022 Northwestern University.
# Copyright (C)      2022 TU Wien.
# Copyright (C)      2022 Graz University of Technology.
#
# Invenio App RDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

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
                "image-previewer": "./less/zenodo_rdm/previewer/image-previewer.less",
            },
            dependencies={
                "@babel/runtime": "^7.9.0",
                "formik": "^2.2.9",
                "i18next": "^20.3.0",
                "i18next-browser-languagedetector": "^6.1.0",
                "prop-types": "^15.7.2",
                "react-i18next": "^11.11.0",
                "react-invenio-forms": "^4.5.0",
                "yup": "^0.32.11",
                "react": "^16.13.0",
                "react-dom": "^16.13.0",
                "lodash": "^4.17.0",
            },
            # aliases={
            #     "@translations/zenodo_rdm": "translations",
            # } TODO
        ),
    },
)
