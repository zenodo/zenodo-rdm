#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# Invenio-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Script to run a Python script in a job on OpenShift."""

import json
import subprocess
import sys
from pathlib import Path

PROGRAM = Path(sys.argv[0]).name
TEMPLATE_NAME = "python-script-runner-template"


def _abort(message):
    print(message)
    sys.exit(1)


if len(sys.argv) < 1:
    print(f"Usage: {PROGRAM} <file> <image>\n")
    print("  file: the path to the script to run")
    print(
        "  image: the image version to be used by the job. If not provided, the script will try to infer it from the deployed image."
    )
    print(f"  Example: {PROGRAM} /home/script.py 7.3.0")
    sys.exit(1)


def infer_deployed_version():
    """Infer which version of Zenodo is currently deployed in 'web'."""
    # oc get deployment web -o json
    res = subprocess.run(
        [
            "oc",
            "get",
            "deployment",
            "web",
            "-o",
            "json",
        ],
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        _abort(f"Failed to get latest deployed image: {res.stderr}")
    deployment_info = json.loads(res.stdout)
    containers = deployment_info["spec"]["template"]["spec"]["containers"]
    filtered = list(filter(lambda x: x["name"] == "web", containers))
    if len(filtered) == 0:
        _abort("No 'web' container found in deployment, can't infer deployed version.")
    elif len(filtered) > 1:
        _abort("Found multiple 'web' containers, can't infer deployed version.")
    image = filtered[0]["image"]
    version = image.replace("ghcr.io/zenodo/zenodo-rdm/zenodo-rdm:", "")
    return version


script_path = sys.argv[1]
image_version = (
    sys.argv[2].removeprefix("v") if len(sys.argv) > 2 else infer_deployed_version()
)

# verify the file exists in local filesystem
if not Path(script_path).is_file():
    _abort(f"File '{script_path}' does not exist.")

# Check OpenShift login
res = subprocess.run(["oc", "whoami"], capture_output=True, text=True)
if res.returncode != 0:
    _abort(f"Not logged in to OpenShift, run `oc login`: {res.stderr}")

# Check the template exists
res = subprocess.run(
    ["oc", "get", "templates", TEMPLATE_NAME],
    capture_output=True,
    text=True,
)
if res.returncode != 0:
    _abort(f"Template '{TEMPLATE_NAME}' not found.")

# Copy the script to the mount /ops (e.g. using a running terminal pod)
terminal_pod = subprocess.run(
    [
        "oc",
        "get",
        "pods",
        "-l",
        "app=terminal",
        "-o",
        "jsonpath='{.items[0].metadata.name}'",
    ],
    capture_output=True,
    text=True,
)
if terminal_pod.returncode != 0:
    _abort("Terminal pod not found.")

terminal_pod_name = terminal_pod.stdout.strip("'")
str_ = f"""
The job will:
- copy the script {script_path} to {terminal_pod_name}
- run a pod with Zenodo {image_version}
- execute the script inside the created pod
Proceed? (y/n):
"""
if input(str_) != "y":
    _abort("Aborted.")


res = subprocess.run(["oc", "cp", script_path, f"{terminal_pod_name}:/ops"])
if res.returncode != 0:
    _abort(f"Failed to copy script to terminal pod: {res.stderr}")

# Use the name of the file as the script name in the terminal pod
script_name = Path(script_path).name

# Run the script in the terminal pod
# oc process python-script-runner-template  -p SCRIPT_PATH=<script_path> | oc create -f -
res = subprocess.run(
    [
        "oc",
        "process",
        TEMPLATE_NAME,
        "-p",
        f"SCRIPT_PATH={script_name}",
        "-p",
        f"ZENODO_VERSION={image_version}",
    ],
    capture_output=True,
)

if res.returncode != 0:
    _abort(f"Failed to process template: {res.stderr}")

res = subprocess.run(
    [
        "oc",
        "create",
        "-f",
        "-",
    ],
    input=res.stdout,
    capture_output=True,
)
if res.returncode != 0:
    _abort(f"Failed to create job: {res.stderr}")
print(res.stdout.decode())
print("Done!")
