#!/usr/bin/env python
import sys
import subprocess
from pathlib import Path


PRGORAM = Path(sys.argv[0]).name
ENVS = {
    "dev": "zenodo-rdm-dev",
    "qa": "zenodo-rdm-qa",
    "prod": "zenodo-rdm",
}
DEPLOYMENTS = {
    "web": ["web", "copy-web-assets"],
    "worker": ["worker"],
    "worker-beat": ["worker-beat"],
}


def _abort(message):
    print(message)
    sys.exit(1)


if len(sys.argv) != 3:
    print(f"Usage: {PRGORAM} <env> <image_tag>\n")
    print(f"  env: one of [{', '.join(ENVS.keys())}]")
    print("  image_tag: the tag of the image to deploy (e.g. `3.1.0`)")
    print()
    print(f"  Example: {PRGORAM} qa 3.1.0")
    sys.exit(1)

env = sys.argv[1]
image_tag = sys.argv[2]

if env not in ENVS:
    _abort(f"Invalid environment: {env}, must be one of {list(ENVS.keys())}")

# Verify image exists
image = f"ghcr.io/zenodo/zenodo-rdm/zenodo-rdm:{image_tag}"

# Check OpenShift login
res = subprocess.run(["oc", "whoami"], capture_output=True, text=True)
if res.returncode != 0:
    _abort(f"Not logged in to OpenShift, run `oc login`: {res.stderr}")


oc_env = ENVS[env]
print(f"You're deploying to {env} ({oc_env}), the following images updates:")
for deployment, containers in DEPLOYMENTS.items():
    print(f"  {deployment}: {containers} -> {image}")
if input("\nType the name of the environment to confirm: ") != env:
    _abort("Deployment aborted!")


for deployment, containers in DEPLOYMENTS.items():
    containers_args = [f"{container}={image}" for container in containers]
    print()
    res = subprocess.run(
        # oc set image deployment/web web=my/repo:v1.0 copy-web-assets=my/repo:v1.0
        [
            "oc",
            "set",
            "image",
            "--namespace",
            oc_env,
            f"deployment/{deployment}",
            *containers_args,
        ],
        capture_output=True,
    )
    print(res.stdout.decode())
