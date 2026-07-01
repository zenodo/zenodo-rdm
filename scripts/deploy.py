#!/usr/bin/env -S uv run --no-project --script
# SPDX-FileCopyrightText: 2024-2025 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
import subprocess
import sys
from pathlib import Path

PROGRAM = Path(sys.argv[0]).name
ENVS = {
    "dev": "zenodo-rdm-dev",
    "qa": "zenodo-rdm-qa",
    "prod": "zenodo-rdm",
}
env_names = ", ".join(ENVS.keys())
DEPLOYMENTS = {
    "web": ["web", "copy-web-assets"],
    "worker": ["worker"],
    "worker-indexing": ["worker-indexing"],
    "worker-low": ["worker-low"],
    "worker-spam": ["worker-spam"],
    "worker-beat": ["worker-beat"],
    "worker-beat-custom": ["worker-beat-custom"],
    "terminal": ["terminal"],
}
# CronJobs run with their image pinned in the manifest, so they go stale unless
# bumped here together with the deployments on every deploy.
CRONJOBS = {
    "export-all-xml": ["terminal"],
    "stats-agg-file-download": ["terminal"],
    "stats-agg-record-view": ["terminal"],
}
# name -> (resource kind, container names)
RESOURCES = {
    **{name: ("deployment", containers) for name, containers in DEPLOYMENTS.items()},
    **{name: ("cronjob", containers) for name, containers in CRONJOBS.items()},
}
resource_names = ", ".join(RESOURCES.keys())


def _abort(message):
    print(message)
    sys.exit(1)


if len(sys.argv) < 3:
    print(f"Usage: {PROGRAM} <env> <image_tag> [<target>...]\n")
    print(f"  env: one of [{env_names}]")
    print("  image_tag: the tag of the image to deploy (e.g. `3.1.0`)")
    print(f"  target: any of [{resource_names}] (optional, default all)")
    print()
    print(f"  Example: {PROGRAM} qa 3.1.0")
    sys.exit(1)

env = sys.argv[1]
if env not in ENVS:
    _abort(f"Invalid environment: {env}, must be one of {env_names}")

image_tag = sys.argv[2]
if not image_tag:
    _abort("Invalid image tag")

if len(sys.argv) > 3:
    targets = sys.argv[3:]
    for target in targets:
        if target not in RESOURCES:
            _abort(f"Invalid target: {target}, must be one of {resource_names}")
else:
    targets = RESOURCES.keys()

# Verify image exists
image = f"ghcr.io/zenodo/zenodo-rdm/zenodo-rdm:{image_tag}"

# Check OpenShift login
res = subprocess.run(["oc", "whoami"], capture_output=True, text=True)
if res.returncode != 0:
    _abort(f"Not logged in to OpenShift, run `oc login`: {res.stderr}")


oc_env = ENVS[env]
print(f"You're deploying to {env} ({oc_env}), the following images updates:")
for name, (kind, containers) in RESOURCES.items():
    if name not in targets:
        continue
    print(f"  {kind}/{name}: {containers} -> {image}")

if input("\nType the name of the environment to confirm: ") != env:
    _abort("Deployment aborted!")


for name, (kind, containers) in RESOURCES.items():
    if name not in targets:
        continue
    containers_args = [f"{container}={image}" for container in containers]
    print()
    res = subprocess.run(
        # oc set image deployment/web web=my/repo:v1.0 copy-web-assets=my/repo:v1.0
        # oc set image cronjob/export-all-xml terminal=my/repo:v1.0
        [
            "oc",
            "set",
            "image",
            "--namespace",
            oc_env,
            f"{kind}/{name}",
            *containers_args,
        ],
        capture_output=True,
    )
    print(res.stdout.decode())
