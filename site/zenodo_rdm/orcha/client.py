import os
import requests


class OrchaClient:
    def __init__(
        self,
        key_path=None,
        key_id=None,
        tenant=None,
        base_url=None,
        public_url=None,
        ssl_verify=True,
    ):
        self.key_path = key_path
        self.key_id = key_id
        self.tenant = tenant
        self.base_url = base_url
        self.public_url = public_url or base_url
        self.ssl_verify = ssl_verify
        self._private_key = None

    @property
    def private_key(self):
        if self._private_key is None:
            key_content = os.environ.get("ZENODO_ORCHA_PRIVATE_KEY")
            if key_content:
                self._private_key = key_content
            elif self.key_path:
                with open(self.key_path) as f:
                    self._private_key = f.read()
            else:
                raise RuntimeError("No private key configured for Orcha client.")
        return self._private_key

    def trigger_workflow(self, payload, token):
        response = requests.post(
            f"{self.base_url}/workflows/",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
            verify=self.ssl_verify,
        )
        response.raise_for_status()
        return response.json()

    def stream_url(self, workflow_id: str, token: str):
        """Create the stream URL for an Orcha workflow."""
        return f"{self.public_url}/workflows/{workflow_id}/stream?token={token}"
