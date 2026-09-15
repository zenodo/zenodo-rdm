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
OUT_FILE="accounts.csv"
RUN_INVENIO="uv run invenio"

echo "email,password" > "${OUT_FILE}"

for ((i = 1;i <= COUNT; i++)); do
    email="locust-${i}@demo.org"
    password="$(LC_ALL=C tr -dc 'A-Za-z0-9' </dev/urandom | head -c 24)"
    echo "Creagin ${email}..."
    ${RUN_INVENIO} users create "${email}" --password "${password}" --active --confirm
    echo "Created ${email}, ${password}"
    echo "${email},${password}" >> "${OUT_FILE}"
done

echo ""
echo "Wrote ${COUNT} accounts to ${OUT_FILE}"
