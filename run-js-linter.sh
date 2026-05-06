#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2022 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

INSTALL=0
FIX=""

for arg in "$@"; do
	case ${arg} in
		-i|--install) INSTALL=1;;
		-f|--fix) FIX="--fix";;
		*)
			printf "Argument ${RED}$arg${NC} not supported\n"
			exit 1;;
	esac
done

# Install lint deps in a project-local hidden dir to avoid peer-dep conflicts
# with the root package.json (which is managed by `invenio-cli assets lock`).
# NODE_PATH points eslint at the dir so it can resolve the shareable config.
LINT_DIR=".lint"
mkdir -p "$LINT_DIR"
cat > "$LINT_DIR/package.json" <<'EOF'
{
	"name": "_lint",
	"private": true,
	"dependencies": {
		"eslint": "^8",
		"@inveniosoftware/eslint-config-invenio": "^2.0.0"
	}
}
EOF

# Only install if forced with `-i` or if we haven't run install before
if [[ ${INSTALL} -eq 1 || ! -d "$LINT_DIR/node_modules" ]]; then
	printf "${GREEN}Install eslint dependencies${NC}\n"
	pnpm --dir "$LINT_DIR" install --shamefully-hoist
fi

printf "${GREEN}Run eslint${NC}\n"
NODE_PATH="$LINT_DIR/node_modules" "$LINT_DIR/node_modules/.bin/eslint" \
	-c .eslintrc.yml --ext .js ${FIX} site/
