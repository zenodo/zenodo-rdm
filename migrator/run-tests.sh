#!/usr/bin/env bash
# -*- coding: utf-8 -*-
#
# Copyright (C) 2016-2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

# Usage:
#   ./run-tests.sh [pytest options and args...]

# Quit on errors
set -o errexit

# Quit on unbound symbols
set -o nounset

python -m check_manifest
eval "$(docker-services-cli up --db ${DB:-postgresql} --env)"
python -m pytest "$@"
tests_exit_code=$?
eval "$(docker-services-cli down --env)"
exit "$tests_exit_code"
