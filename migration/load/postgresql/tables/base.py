import json
import uuid
from abc import ABC, abstractmethod
from dataclasses import fields
from datetime import datetime


def as_csv_row(dc):
    """Serialize a dataclass instance as a CSV-writable row."""
    row = []
    for f in fields(dc):
        val = getattr(dc, f.name)
        if val:
            if issubclass(f.type, (dict,)):
                val = json.dumps(val)
            elif issubclass(f.type, (datetime,)):
                val = val.isoformat()
            elif issubclass(f.type, (uuid.UUID,)):
                val = str(val)
        row.append(val)
    return row

    
class PostgreSQLTableLoad(ABC):
    """Create CSV files with table create and inserts.
    
    Computes the rows based on the loaders attributes (e.g. parent_cache).
    """

    def __init__(self, tables):
        """Constructor."""
        self.tables = tables
        
    @abstractmethod
    def _generate_db_tuples(self, **kwargs):
        """Yield generated tuples."""
        pass

    @abstractmethod
    def prepare(self, output_dir, **kwargs):
        """Compute rows."""
        pass

    def cleanup(self, **kwargs):
        """Cleanup."""
        # not abstract to not require its implementation
        pass