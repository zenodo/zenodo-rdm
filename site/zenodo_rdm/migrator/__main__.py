import sys

from invenio_rdm_migrator.streams import Runner

from .stream import (
    CommunitiesStreamDefinition,
    RecordStreamDefinition,
    UserStreamDefinition,
)


if __name__ == "__main__":

    runner = Runner(
        stream_definitions=[
            UserStreamDefinition,
            CommunitiesStreamDefinition,
            RecordStreamDefinition,
        ],
        config_filepath=sys.argv[1],
    )
    runner.run()
