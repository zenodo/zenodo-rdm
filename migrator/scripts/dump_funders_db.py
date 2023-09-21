"""Parse funders from ROR dumps into CSV format, importable via COPY.

A modified version of https://github.com/inveniosoftware/invenio-vocabularies/blob/master/invenio_vocabularies/contrib/funders/datastreams.py
for the purpose of producing an easy to load CSV dump of the awards into an InvenioRDM instance.

To use call ``load_file(DATA_PATH, "funders.csv")``.
"""

import csv
import uuid

import orjson
from idutils import normalize_ror
from invenio_rdm_migrator.utils import ts

DATA_PATH = "v1.32-2023-09-14-ror-data.zip"  # https://zenodo.org/record/8346986


VOCABULARIES_FUNDER_SCHEMES = {
    "grid",
    "gnd",
    "isni",
    "ror",
    "doi",
    "fundref",
}


def transform_funder(data):
    """Applies the transformation to the stream entry."""
    funder = {
        "$schema": "local://funders/funder-v1.0.0.json",
    }

    funder["id"] = normalize_ror(data.get("id"))
    if not funder["id"]:
        return

    funder["name"] = data.get("name")
    if not funder["name"]:
        return

    country_code = data.get("country", {}).get("country_code")
    if country_code:
        funder["country"] = country_code

    funder["title"] = {"en": funder["name"]}
    for label in data.get("labels", []):
        funder["title"][label["iso639"]] = label["label"]

    # The ROR is always listed in identifiers, expected by serialization
    funder["identifiers"] = [{"identifier": funder["id"], "scheme": "ror"}]
    for scheme, identifier in data.get("external_ids", {}).items():
        scheme = scheme.lower()
        if scheme in VOCABULARIES_FUNDER_SCHEMES:
            value = identifier.get("preferred") or identifier.get("all")[0]
            if scheme == "fundref":
                value = f"10.13039/{value}"
                scheme = "doi"

            funder["identifiers"].append(
                {
                    "identifier": value,
                    "scheme": scheme,
                }
            )

    return funder


def load_file(datafile, outpath):
    """Load the data file and dump as CSV."""
    with open(outpath, "w") as fout, open(datafile, "rb") as fp:
        print(f"[{ts()}] loading {datafile}")
        writer = csv.writer(fout)
        entries = orjson.loads(fp.read())
        for idx, data in enumerate(entries):
            if idx % 1000 == 0:
                print(f"[{ts()}] {idx}")
            try:
                funder = transform_funder(data)
                if not funder:
                    print(f"[{ts()}] Failed to transform #{idx}:\n{data}\n")
                    continue
                funder_id = funder.pop("id")
                creation_ts = ts()
                writer.writerow(
                    (
                        str(uuid.uuid4()),  # id
                        funder_id,  # pid
                        orjson.dumps(funder).decode("utf-8"),  # json
                        creation_ts,  # created
                        creation_ts,  # updated (same as created)
                        1,  # version_id
                    )
                )
            except Exception as ex:
                print(f"[{ts()}] Exception for line {idx}:\n{data}\n\n{ex}\n")
