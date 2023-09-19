"""Parse affiliations from ROR dumps into CSV format, importable via COPY.

To use call ``load_file(DATA_PATH, "affiliations.csv")``.
"""

import csv
import orjson as json
import uuid

from idutils import normalize_ror
from invenio_rdm_migrator.utils import ts

DATA_PATH = "v1.32-2023-09-14-ror-data.zip"  # https://zenodo.org/record/8346986


VOCABULARIES_AFFILIATION_SCHEMES = {
    "grid",
    "gnd",
    "isni",
    "ror",
}


def transform_affiliation(data):
    """Applies the transformation to the stream entry."""
    affiliation = {
        "$schema": "local://affiliations/affiliation-v1.0.0.json",
    }

    affiliation["id"] = normalize_ror(data.get("id"))
    if not affiliation["id"]:
        return

    affiliation["name"] = data.get("name")
    if not affiliation["name"]:
        return

    acronyms = data.get("acronyms") or []
    if acronyms:
        affiliation["acronym"] = acronyms[0]

    affiliation["title"] = {"en": affiliation["name"]}
    for label in data.get("labels", []):
        affiliation["title"][label["iso639"]] = label["label"]

    # The ROR is always listed in identifiers, expected by serialization
    affiliation["identifiers"] = [{"identifier": affiliation["id"], "scheme": "ror"}]
    for scheme, identifier in data.get("external_ids", {}).items():
        scheme = scheme.lower()
        if scheme in VOCABULARIES_AFFILIATION_SCHEMES:
            value = identifier.get("preferred") or identifier.get("all")[0]
            affiliation["identifiers"].append({"identifier": value, "scheme": scheme})

    return affiliation


def load_file(datafile, outpath):
    """Load the data file and dump as CSV."""
    with open(outpath, "w") as fout, open(datafile, "rb") as fp:
        print(f"[{ts()}] loading {datafile}")
        writer = csv.writer(fout)
        entries = json.loads(fp.read())
        for idx, data in enumerate(entries):
            if idx % 1000 == 0:
                print(f"[{ts()}] {idx}")
            try:
                affiliation = transform_affiliation(data)
                if not affiliation:
                    print(f"[{ts()}] Failed to transform #{idx}:\n{data}\n")
                    continue
                affiliation_id = affiliation.pop("id")
                creation_ts = ts()
                writer.writerow(
                    (
                        str(uuid.uuid4()),  # id
                        affiliation_id,  # pid
                        json.dumps(affiliation),  # json
                        creation_ts,  # created
                        creation_ts,  # updated (same as created)
                        1,  # version_id
                    )
                )
            except Exception as ex:
                print(f"[{ts()}] Exception for line {idx}:\n{data}\n\n{ex}\n")
