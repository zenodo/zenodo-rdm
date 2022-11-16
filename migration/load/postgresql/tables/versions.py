import csv

from ...dataclasses import RDMVersionState
from .base import PostgreSQLTableLoad, as_csv_row


class RDMVersionStateComputedTable(PostgreSQLTableLoad):
    """RDM version state computed table."""

    def __init__(self, parent_cache):
        """Constructor."""
        super().__init__(
            tables=[RDMVersionState._table_name]
        )
        self.parent_cache = parent_cache

    def _generate_db_tuples(self, **kwargs):
        for parent_id, parent_state in self.parent_cache.items():
            # Version state to be populated in the end from the final state
            yield RDMVersionState(
                latest_index=parent_state["version"]["latest_index"],
                parent_id=parent_state["id"],
                latest_id=parent_state["version"]["latest_id"],
                next_draft_id=None,
            )

    def prepare(self, output_dir, **kwargs):
        """Compute rows."""
        fpath = output_dir / f"rdm_versions_state.csv"
        with open(fpath, "a") as fp:
            writer = csv.writer(fp)
            for entry in self._generate_db_tuples():
                writer.writerow(as_csv_row(entry))

        return self.tables