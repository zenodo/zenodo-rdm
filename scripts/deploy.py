#!/usr/bin/env python
import sys
import subprocess
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
    "worker-low": ["worker-low"],
    "worker-spam": ["worker-spam"],
    "worker-beat": ["worker-beat"],
    "terminal": ["terminal"],
}
deployment_names = ", ".join(DEPLOYMENTS.keys())

def _abort(message):
    print(message)
    sys.exit(1)


if len(sys.argv) < 3:
    print(f"Usage: {PROGRAM} <env> <image_tag> [<deployment>...]\n")
    print(f"  env: one of [{env_names}]")
    print("  image_tag: the tag of the image to deploy (e.g. `3.1.0`)")
    print(f"  deployment: any of [{deployment_names}] (optional, default all)")
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
    deployments = sys.argv[3:]
    for dep in deployments:
        if dep not in DEPLOYMENTS:
            _abort(f"Invalid deployment: {dep}, must be one of {deployment_names}")
else:
    deployments = DEPLOYMENTS.keys()

# Verify image exists
image = f"ghcr.io/zenodo/zenodo-rdm/zenodo-rdm:{image_tag}"

# Check OpenShift login
res = subprocess.run(["oc", "whoami"], capture_output=True, text=True)
if res.returncode != 0:
    _abort(f"Not logged in to OpenShift, run `oc login`: {res.stderr}")


oc_env = ENVS[env]
print(f"You're deploying to {env} ({oc_env}), the following images updates:")
for dep, containers in DEPLOYMENTS.items():
    if dep not in deployments:
        continue
    print(f"  {dep}: {containers} -> {image}")

if input("\nType the name of the environment to confirm: ") != env:
    _abort("Deployment aborted!")


for dep, containers in DEPLOYMENTS.items():
    if dep not in deployments:
        continue
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
            f"deployment/{dep}",
            *containers_args,
        ],
        capture_output=True,
    )
    print(res.stdout.decode())
