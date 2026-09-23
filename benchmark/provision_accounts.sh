#!/usr/bin/env bash
# One-time setup: create a pool of already-confirmed, login-able test
# accounts for the Loucst write/authenticated-read scenarios.
#
# Usage:
#    ./provision_accounts.sh [num_accounts]
#
# Writes email, password pairs to benchmark/accounts.csv (gitignored)
# TODO: Pipe it to dev or sandbox 

COUNT="${1:-10}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"  && pwd)"
OUT_FILE="${SCRIPT_DIR}/accounts.csv"
RUN_INVENIO="uv run invenio"

echo "email,password" > "${OUT_FILE}"
CREATED=0

for ((i = 1;i <= COUNT; i++)); do
    email="locust-${i}@demo.org"
    password="$(LC_ALL=C tr -dc 'A-Za-z0-9' </dev/urandom | head -c 24)"
    echo "Creagin ${email}..."
    if ${RUN_INVENIO} users create "${email}" --password "${password}" --active --confirm; then
        echo "Created ${email}, ${password}"
        echo "${email},${password}" >> "${OUT_FILE}"
        ((CREATED++))
    else
        echo "Failed to create ${email}, skipping" >&2
    fi
done

echo ""
echo "Wrote ${CREATED} accounts to ${OUT_FILE}"
