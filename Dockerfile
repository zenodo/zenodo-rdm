#-*- coding: utf-8 -*-
#
# This file is part of Invenio.
#
# Copyright (C) 2019-2020 CERN.
# Copyright (C) 2019-2020 Northwestern University.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
# Dockerfile that builds a fully functional image of your app.
#
# This image installs all Python dependencies for your application. It's based
# on CentOS 7 with Python 3 (https://github.com/inveniosoftware/docker-invenio)
# and includes Pip, Pipenv, Node.js, NPM and some few standard libraries
# Invenio usually needs.
#
# Note: It is important to keep the commands in this file in sync with your
# bootstrap script located in ./scripts/bootstrap.

FROM inveniosoftware/centos7-python:3.6

COPY Pipfile Pipfile.lock ./
RUN pipenv install --deploy --system

# TODO: Remove when invenio-communities git dependency works
COPY requirements-devel.txt ./
RUN pip install -r requirements-devel.txt

COPY ./ .
COPY ./docker/uwsgi/ ${INVENIO_INSTANCE_PATH}
COPY ./invenio.cfg ${INVENIO_INSTANCE_PATH}
COPY ./templates/ ${INVENIO_INSTANCE_PATH}/templates/
COPY ./static/. ${INVENIO_INSTANCE_PATH}/static/
COPY ./assets/. ${INVENIO_INSTANCE_PATH}/assets/
RUN invenio collect --verbose && \
    invenio webpack create && \
    # --unsafe needed because we are running as root
    invenio webpack install --unsafe && \
    invenio webpack build

ENTRYPOINT [ "bash", "-c"]
