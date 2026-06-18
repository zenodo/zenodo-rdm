#!/usr/bin/env -S uv run --no-project --script
# SPDX-FileCopyrightText: 2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Render a zenodo/ops deployment checklist issue body from changelog.py --json (stdin)."""

import argparse
import json
import re
import sys
from pathlib import PurePosixPath

# (section title, hostname, deploy.py env)
ENVS = [
    ("QA", "sandbox.zenodo.org", "qa"),
    ("Prod", "zenodo.org", "prod"),
]


def _web(repo_url):
    """Normalize a git remote URL to an https GitHub web base, or None."""
    if not repo_url:
        return None
    url = repo_url.removesuffix(".git")
    if url.startswith("git@github.com:"):
        url = "https://github.com/" + url[len("git@github.com:") :]
    return url


def _compare(p):
    """`name prev → cur`, linked to the GitHub compare when we have the tags."""
    label = f"{p['name']} {p['prev']} → {p['cur']}"
    web, prev_tag, cur_tag = _web(p.get("repo")), p.get("prev_tag"), p.get("cur_tag")
    if web and prev_tag and cur_tag:
        return f"[{label}]({web}/compare/{prev_tag}...{cur_tag})"
    return label


def _file_link(p, path):
    """File name linked to its content at the new tag."""
    name = PurePosixPath(path).name
    web, cur_tag = _web(p.get("repo")), p.get("cur_tag")
    if web and cur_tag:
        return f"[{name}]({web}/blob/{cur_tag}/{path})"
    return name


# Mapping files live at <module>/.../mappings/<engine>/<path>/<name>-vX.Y.Z.json.
# The index name is <path>/<name>-vX.Y.Z with slashes turned into dashes.
_VERSION = re.compile(r"-v\d+\.\d+\.\d+$")
_REVISION = re.compile(r"^[0-9a-f]{6,}$")


def _index_name(path):
    parts = PurePosixPath(path).parts
    if "mappings" not in parts:
        return None
    rel = parts[parts.index("mappings") + 2 :]  # drop "mappings" and the engine dir
    return "-".join(rel).removesuffix(".json") if rel else None


def index_update_cmds(packages):
    """One `invenio index update` per changed index, at its highest (live) version."""
    names = set()
    for p in packages:
        for f in p.get("mappings") or []:
            if name := _index_name(f):
                names.add(name)
    best = {}  # family -> (version tuple, full name)
    for name in names:
        m = _VERSION.search(name)
        family = name[: m.start()] if m else name
        ver = tuple(int(n) for n in re.findall(r"\d+", m.group())) if m else (0,)
        if family not in best or ver > best[family][0]:
            best[family] = (ver, name)
    return [f"invenio index update --no-check {n}" for _, n in sorted(best.values())]


def alembic_upgrades(packages):
    """Detected Alembic revisions as `module@revision` (the filename prefix).

    Sorted, which groups by module and — since recent revisions are timestamps —
    orders each module's revisions into apply order (oldest first, head last).
    """
    revs = set()
    for p in packages:
        for f in p.get("alembic") or []:
            fname = PurePosixPath(f).name
            rev = fname.split("_", 1)[0]
            if not fname.endswith(".py") or not _REVISION.match(rev):
                continue
            revs.add(f"{PurePosixPath(f).parts[0]}@{rev}")
    return sorted(revs)


def changes_to_check(packages):
    def is_major(p):
        return p.get("bump") == "major"

    inv_major = [p for p in packages if is_major(p) and p.get("matched_filter")]
    other_major = [p for p in packages if is_major(p) and not p.get("matched_filter")]
    alembic = [p for p in packages if p.get("alembic")]
    mappings = [p for p in packages if p.get("mappings")]

    lines = ["### What to check"]
    if not (inv_major or other_major or alembic or mappings):
        lines.append(
            "- Nothing flagged automatically. Still skim the diff before you sign off."
        )
        return lines

    if inv_major:
        lines.append("- ⚠️ Major `invenio-*` bumps in...")
        lines += [f"    - {_compare(p)}" for p in inv_major]
    if other_major:
        lines.append("- ⚠️ Major bumps in other dependencies...")
        lines += [f"    - {p['name']} {p['prev']} → {p['cur']}" for p in other_major]
    if alembic:
        lines.append("- DB migration (Alembic recipe) changes in...")
        for p in alembic:
            lines.append(f"    - {p['name']}")
            lines += [f"        - {_file_link(p, f)}" for f in p["alembic"]]
    if mappings:
        lines.append("- Mapping changes in...")
        for p in mappings:
            lines.append(f"    - {p['name']}")
            lines += [f"        - {_file_link(p, f)}" for f in p["mappings"]]
    return lines


def env_section(name, host, env, image_tag, index_cmds, alembic_revs, author):
    lines = [
        f"### {name} ({host})",
        "",
        "#### Pre-deploy steps",
        f"- [ ] No pre-deploy steps needed, confirmed by @{author}",
    ]
    if env == "prod":
        lines.append("- 📝 Otherwise, paste the steps you confirmed on QA above.")
    else:
        lines.append("- 📝 Otherwise, tick each step below as you do it:")
        lines.append("- [ ] Config changes 📝")
        lines.append("- [ ] Alembic")
        if alembic_revs:
            lines += [f"    - [ ] `invenio alembic upgrade {r}`" for r in alembic_revs]
        else:
            lines.append("    - [ ] `invenio alembic upgrade <module>@<rev>` 📝")
        lines.append("- [ ] Index update")
        if index_cmds:
            lines += [f"    - [ ] `{c}`" for c in index_cmds]
        else:
            lines.append("    - [ ] `invenio index update --no-check <index>` 📝")
        lines.append("- [ ] Reindex")
        lines.append("    - [ ] `invenio rdm rebuild-all-indices -o <model>` 📝")
        lines.append("- [ ] Vocabularies / fixtures / custom fields 📝")
    lines += [
        "",
        "#### Deploy",
        f"- [ ] `./scripts/deploy.py {env} {image_tag} terminal` "
        f"then `./scripts/deploy.py {env} {image_tag}`",
        "",
        "#### Post-deploy",
        "- [ ] Monitor Sentry",
        "- [ ] Run verification queries",
        "",
    ]
    return lines


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True, help="Release tag, e.g. v25.0.0")
    parser.add_argument("--since", default="", help="Previous tag, e.g. v24.5.1")
    parser.add_argument(
        "--author", default="author", help="GitHub handle to credit in the sign-off"
    )
    args = parser.parse_args()

    data = json.load(sys.stdin)
    packages = data.get("packages", [])

    version = args.version
    image_tag = version.lstrip("v")  # deploy.py / the image tag drops the leading "v"
    prev = args.since or data.get("since") or ""
    rng = f"`{prev}..{version}`" if prev else f"`{version}`"

    index_cmds = index_update_cmds(packages)
    alembic_revs = alembic_upgrades(packages)

    body = [
        f"Auto-generated from {rng}.",
        "Run the checklist on QA first, then copy the confirmed steps into Prod.",
        "",
        *changes_to_check(packages),
        "",
    ]
    for name, host, env in ENVS:
        body += env_section(
            name, host, env, image_tag, index_cmds, alembic_revs, args.author
        )

    sys.stdout.write("\n".join(body).rstrip() + "\n")


if __name__ == "__main__":
    main()
