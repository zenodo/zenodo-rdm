#!/usr/bin/env sh
# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2023 CERN.
#
# Demo-InvenioRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

# Quit on errors
set -o errexit

# Quit on unbound symbols
set -o nounset

# Wipe
# ----

invenio shell --no-term-title -c "import redis; redis.StrictRedis.from_url(app.config['CACHE_REDIS_URL']).flushall(); print('Cache cleared')"
# NOTE: db destroy is not needed since DB keeps being created
#       Just need to drop all tables from it.
invenio db drop --yes-i-know
invenio index destroy --force --yes-i-know
invenio index queue init purge

# Recreate
# --------
# NOTE: db init is not needed since DB keeps being created
#       Just need to create all tables from it.
invenio db create
# TODO: add back when pipenv access problem is fixed
#invenio files location create --default 'default-location'  $(pipenv run invenio shell --no-term-title -c "print(app.instance_path)")'/data'
invenio files location create --default 'default-location' /opt/invenio/var/instance/data
invenio roles create admin
invenio access allow superuser-access role admin
invenio index init --force
invenio rdm-records custom-fields init
invenio communities custom-fields init

# Add demo and fixtures data
# -------------
invenio rdm-records fixture
psql << "DELETE FROM accounts_user WHERE id=1;"  # remove admin@inveniosoftware.org
# invenio rdm-records demo
invenio vocabularies import -v names -f ./app_data/vocabularies-future.yaml  # zenodo specific names

# Enable admin user
# invenio users activate admin@inveniosoftware.org
