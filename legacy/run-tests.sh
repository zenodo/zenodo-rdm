#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2016-2023 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
set -o errexit

# Quit on unbound symbols
set -o nounset

python -m check_manifest
python -m pytest "$@"
tests_exit_code=$?
exit "$tests_exit_code"
