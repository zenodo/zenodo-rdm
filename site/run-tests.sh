#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2016-2023 CERN
# SPDX-FileCopyrightText: 2020 Northwestern University
# SPDX-FileCopyrightText: 2021 TU Wien
# SPDX-FileCopyrightText: 2022 Graz University of Technology
# SPDX-License-Identifier: GPL-3.0-or-later
set -o errexit

# Quit on unbound symbols
set -o nounset

# Define function for bringing down services
function cleanup {
  eval "$(docker-services-cli down --env)"
}

# Check for arguments
# Note: "-k" would clash with "pytest"
keep_services=0
pytest_args=()
for arg in $@; do
	# from the CLI args, filter out some known values and forward the rest to "pytest"
	# note: we don't use "getopts" here b/c of some limitations (e.g. long options),
	#       which means that we can't combine short options (e.g. "./run-tests -Kk pattern")
	case ${arg} in
		-K|--keep-services)
			keep_services=1
			;;
		*)
			pytest_args+=( ${arg} )
			;;
	esac
done

if [[ ${keep_services} -eq 0 ]]; then
	trap cleanup EXIT
fi

eval "$(docker-services-cli up --db ${DB:-postgresql} --search ${SEARCH:-opensearch} --mq ${MQ:-rabbitmq} --cache ${CACHE:-redis} --env)"
# Note: expansion of pytest_args looks like below to not cause an unbound
# variable error when 1) "nounset" and 2) the array is empty.
python -m pytest ${pytest_args[@]+"${pytest_args[@]}"}
tests_exit_code=$?
exit "$tests_exit_code"
