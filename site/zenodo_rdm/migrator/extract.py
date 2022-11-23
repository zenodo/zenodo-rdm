import json

from invenio_rdm_migrator.extract import Extract


class JSONLExtract(Extract):
    """Data extraction from JSONL files."""

    def __init__(self, filepath):
        """Constructor."""
        self.filepath = filepath

    def run(self):
        """Yield one element at a time."""
        with open(self.filepath, 'r') as reader:
            for l in reader:
                # TODO JSONl file should be cleaned up before loading
                l = l.strip().replace("\\\\","\\")
                yield json.loads(l)