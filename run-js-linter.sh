#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2022 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

FIX=""

for arg in "$@"; do
	case ${arg} in
		-f|--fix) FIX="--fix";;
		*)
			printf "Argument ${RED}$arg${NC} not supported\n"
			exit 1;;
	esac
done

printf "${GREEN}Run eslint${NC}\n"
npx --yes -p @inveniosoftware/eslint-config-invenio@2.0.0 -p eslint@^8 eslint -c .eslintrc.yml --ext .js ${FIX} site/
