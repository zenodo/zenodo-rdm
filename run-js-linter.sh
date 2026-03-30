#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2022 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

for arg in $@; do
	case ${arg} in
		-i|--install)
			npm install --no-save --no-package-lock @inveniosoftware/eslint-config-invenio@^2.0.0;;
		-f|--fix)
			printf "${GREEN}Run eslint${NC}\n";
			npx eslint -c .eslintrc.yml site/zenodo_rdm/**/*.js --fix;;
		*)
			printf "Argument ${RED}$arg${NC} not supported\n"
			exit;;
	esac
done

printf "${GREEN}Run eslint${NC}\n"
npx eslint -c .eslintrc.yml --ext .js site/
