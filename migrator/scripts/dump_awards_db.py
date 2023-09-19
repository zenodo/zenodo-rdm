"""Parse OpenAIRE awards dumps into CSV format, importable via COPY.

A modified version of https://github.com/inveniosoftware/invenio-vocabularies/blob/master/invenio_vocabularies/contrib/awards/datastreams.py
for the purpose of producing an easy to load CSV dump of the awards into an InvenioRDM instance.

To use call ``load_files(DATA_PATHS, "awards.csv")``.
"""
import csv
import gzip
import json
import uuid

from invenio_rdm_migrator.utils import ts

DATA_PATHS = [
    "awards-2023-08.jsonl.gz",  # https://zenodo.org/record/8224080
    "awards-2023-04.jsonl.gz",  # https://zenodo.org/record/7870151
    "awards-2023-03.jsonl.gz",  # https://zenodo.org/record/7803150
    "awards-2023-02.jsonl.gz",  # https://zenodo.org/record/7683844
    "awards-2023-01.jsonl.gz",  # https://zenodo.org/record/7561801
    "awards-2022-12.jsonl.gz",  # https://zenodo.org/record/7745773
]

VOCABULARIES_AWARDS_OPENAIRE_FUNDERS = {
    "aka_________": "05k73zm37",
    "anr_________": "00rbzpz17",
    "arc_________": "05mmh0f86",
    "asap________": "03zj4c476",
    "cihr________": "01gavpb45",
    "corda_______": "00k4n6c32",
    "corda_____he": "00k4n6c32",
    "corda__h2020": "00k4n6c32",
    "euenvagency_": "02k4b9v70",
    "fct_________": "00snfqn58",
    "fwf_________": "013tf3c58",
    "inca________": "03m8vkq32",
    "irb_hr______": "03n51vw80",
    "mestd_______": "01znas443",
    "nhmrc_______": "011kf5r70",
    "nih_________": "01cwqze88",
    "nserc_______": "01h531d29",
    "nsf_________": "021nxhr62",
    "nwo_________": "04jsz6e67",
    "rcuk________": "00dq2kk65",
    "sfi_________": "0271asj38",
    "snsf________": "00yjd3n13",
    "sshrc_______": "006cvnv84",
    "tubitakf____": "04w9kkr77",
    "ukri________": "001aqnf71",
    "wt__________": "029chgv08",
}
VOCABULARIES_AWARDS_EC_ROR_ID = "00k4n6c32"


def transform_openaire_grant(data):
    """Applies the transformation to the stream entry."""
    award = {
        "$schema": "local://awards/award-v1.0.0.json",
    }

    code = data["code"]
    openaire_funder_prefix = data["id"].split("::")[0].split("|")[1]
    funder_id = VOCABULARIES_AWARDS_OPENAIRE_FUNDERS.get(openaire_funder_prefix)
    if funder_id is None:
        return

    award["id"] = f"{funder_id}::{code}"

    funding = next(iter(data.get("funding", [])), None)
    if funding:
        funding_stream_id = funding.get("funding_stream", {}).get("id", "")
        # Example funding stream ID: `EC::HE::HORIZON-AG-UN`. We need the `EC`
        # string, i.e. the second "part" of the identifier.
        program = next(iter(funding_stream_id.split("::")[1:2]), "")
        if program:
            award["program"] = program

    identifiers = []
    if funder_id == VOCABULARIES_AWARDS_EC_ROR_ID:
        identifiers.append(
            {
                "identifier": f"https://cordis.europa.eu/projects/{code}",
                "scheme": "url",
            }
        )
    elif data.get("websiteurl"):
        identifiers.append({"identifier": data.get("websiteurl"), "scheme": "url"})

    if identifiers:
        award["identifiers"] = identifiers

    award["number"] = code
    award["title"] = {"en": data["title"]}
    award["funder"] = {"id": funder_id}
    acronym = data.get("acronym")
    if acronym:
        award["acronym"] = acronym

    return award


def load_files(file_paths, outpath):
    """Load the data files and dump as a single CSV."""
    parsed_award_ids = set()
    with open(outpath, "w") as fout:
        writer = csv.writer(fout)
        for f in file_paths:
            print(f"[{ts()}] loading {f}")
            with open(f, "rb") as fp, gzip.open(fp) as gp:
                for idx, line in enumerate(gp):
                    if idx % 1000 == 0:
                        print(f"[{ts()}] {idx}")
                    try:
                        data = json.loads(line)
                        award = transform_openaire_grant(data)
                        if not award:
                            print(f"[{ts()}] Failed to transform line {idx}:\n{data}\n")
                            continue
                        award_id = award.pop("id")
                        # skip awards that were already parsed
                        if award_id in parsed_award_ids:
                            continue
                        else:
                            parsed_award_ids.add(award_id)
                            creation_ts = ts()
                            writer.writerow(
                                (
                                    str(uuid.uuid4()),  # id
                                    award_id,  # pid
                                    json.dumps(award),  # json
                                    creation_ts,  # created
                                    creation_ts,  # updated (same as created)
                                    1,  # version_id
                                )
                            )
                    except Exception as ex:
                        print(f"[{ts()}] Exception for line {idx}:\n{line}\n\n{ex}\n")
