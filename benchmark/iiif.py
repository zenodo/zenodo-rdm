from locust import HttpUser, task, between
import random
import json
from pathlib import Path

cur_dir = Path(__file__).parent
manifest_path = cur_dir / "manifest.json"

# Load the manifest
if not manifest_path.exists():
    raise FileNotFoundError(
        f"IIIF Manifest file not found at {manifest_path}.\n\n"
        "You can download the manifest from `/api/iiif/record:{id}/manifest` of the "
        "Zenodo instance you're testing."
    )

MANIFEST = json.load(manifest_path.open())
CANVASES = [c for c in MANIFEST["sequences"][0]["canvases"] if "height" in c]


class ImageEndpointUser(HttpUser):
    wait_time = between(1, 2)

    @task
    def access_image_endpoint(self):
        item = random.choice(CANVASES)
        base_url = item["images"][0]["resource"]["service"]["@id"]

        x = random.randint(1, item["width"] - 1)
        y = random.randint(1, item["height"] - 1)
        h = random.randint(1, 1000)
        w = random.randint(1, 1000)
        s = 256 * random.choice([1, 2, 4, 8])
        r = random.choice([0, 90, 180, 270])
        random_slice = f"{base_url}/{x},{y},{h},{w}/^{s},/{r}/default.jpg"
        thumbnail = f"{base_url}/full/^250,/0/default.jpg"
        info_json = f"{base_url}/info.json"

        self.client.get(random_slice, name="/iiif/random_chunk")
        self.client.get(thumbnail, name="/iiif/thumbnail")
        self.client.get(info_json, name="/iiif/info.json")
