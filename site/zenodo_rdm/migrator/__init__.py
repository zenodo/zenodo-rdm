import sys

from stream import RecordStream


if __name__ == "__main__":

    filename = sys.argv[1]
    cleanup = len(sys.argv) > 2  # if there is something we assume is True/--cleanup
    stream = RecordStream(
        filename=filename,
        db_uri="postgresql://zenodo:zenodo@localhost:5432/zenodo",
        output_path="/Users/ppanero/Workspace/zenodo/zenodo-rdm/migration/data/",
    )    
    stream.run(cleanup=cleanup)