# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# Invenio-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Script to run a Python script in a job on OpenShift."""
#!/usr/bin/env python
import subprocess
import sys
from pathlib import Path

PROGRAM = Path(sys.argv[0]).name
TEMPLATE_NAME = "python-script-runner-template"


def _abort(message):
    print(message)
    sys.exit(1)


if len(sys.argv) < 1:
    print(f"Usage: {PROGRAM} <file>\n")
    print(f"  file: the path to the script to run")
    print(f"  Example: {PROGRAM} /home/script.py")
    sys.exit(1)


script_path = sys.argv[1]

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
if input(f"Copy script {script_path} to {terminal_pod_name}? (y/n): ") != "y":
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
