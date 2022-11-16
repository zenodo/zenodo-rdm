import json

from .base import Extract


class JSONLExtract(Extract):
    """Data extraction from JSONL files."""

    def __init__(self, filepath):
        """Constructor."""
        self.filepath = filepath

    def run(self):
        """Yield one element at a time."""
        with open(self.filename, 'r') as reader:
            for l in reader:
                # TODO JSONl file should be cleaned up before loading
                l = l.strip().replace("\\\\","\\")
                yield json.loads(l)
