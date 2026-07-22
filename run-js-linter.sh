#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2022 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
set -euo pipefail

INSTALL=0
SCRIPT="lint"

for arg in "$@"; do
	case "$arg" in
		-i|--install) INSTALL=1 ;;
		-f|--fix) SCRIPT="lint:fix" ;;
		*) echo "Unknown argument: $arg" >&2; exit 1 ;;
	esac
done

SITE="$(dirname -- "${BASH_SOURCE[0]}")/site"

if [[ $INSTALL -eq 1 || ! -d "$SITE/node_modules" ]]; then
	pnpm --dir "$SITE" install
fi

pnpm --dir "$SITE" "$SCRIPT"
