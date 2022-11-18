# To RDM migration

## How to run it

To run the migration you need:

- A running InvenioRDM instance. It is also required to run the setup step to have the vocabularies and other referenced items. For example `invenio-cli services setup --force --no-demo-data`.
- Install the dependencies of the migration code:

```bash
$ pip install -r migration/requirements.txt
```

- Edit the code where the db credentials are hardcoded (right now they are `zenodo:zenodo`, replace by your instances')
- Run the migration ETL. In the existing case it requires JSONLines file with the records.

```bash
$ python run.py data/records-dump.jsonl
```

This will read from the jsonlines file, transform the entries to the RDM data model, output csv files with the data to load on the db (available in `/data/tables`), then perform a `COPY` operation to the DB. The created CSV files are suffixed with the timestamp, so there will be no clash between runs. However, if you wish to delete those files after running the migration, add the `--cleanup` flag to the run command from above.

## Implement your {Extract/Transform/Load}

The package contains 4 folders and one main python file. The `data` folder is meant to host your data and the output of the process (e.g. `tables/`) and it is not version controlled.

The `run.py` file is where the ETL stream is defined and executed. You can hook in your custom extract, transform and load as long as they respect the contract for returning an iterator (so the `Stream.run` function works).

Imagine you wish to read from an XML file and then transform it to RDM data model, so the load process stays the same.

```python
    stream = Stream(
        extract=XMLExtract(filename),
        transform=XMLToRDMRecordTransform(),
        load=PostgreSQLCopyLoad(),
    )
```

How to define the `XMLExtract` and `XMLToRDMRecordTransform` classes is explained in the following sections:

### Extract

The extract is the first part of the data processing stream. It's functionality is quite simple: return an iterator of records, where each record is a dictionary. For example, to implement the `XMLExtract` class:

```python
class XMLExtract(Extract):
    ...

    def run(self):
        with open("file.xml") as file:
            for entry in file:
                yield xml.loads(entry)
```

It is up to discussion if the _transformation_ from XML/JSON string to dictionary should be part of the extract or is it a "pre-transform" step.

### Transform

The transformer has the biggest part of the code logic. It is in charge of making whatever entry it gets into something that can be imported into an RDM database (e.g. an RDMRecord). It's main functionality is to loop through the entries (i.e. the iterator returned by the extract class), transform and yield (e.g. the record). Diving more in the example of a record:

To transform something to an RDM record, you need to implement `transform/base:RDMRecordTransform`. For each record it will yield what is considered a semantically "full" record: the record itself, its parent, its draft in case it exists and the files related them.

```python
{
    "record": self._record(entry),
    "draft": self._draft(entry),
    "parent": self._parent(entry),
    "record_files": self._record_files(entry),
    "draft_files": self._draft_files(entry),
}
```

This means that you will need to implement the functions for each key. Note that, only `_record` and `_parent` should return content, the others can return `None`. In this case we will need to rethink which methods should be `abstractmethod` and which ones be defaulted to `None/{}/some other default` in the base). You can find an example implementation at `transform/zenodo:ZenodoToRDMRecordTransform`.

Some of these functions can themselves use a `transform/base:Entry` transformer. An _entry_ transformer, is one layer deeper abstraction, to provide an interface with the methods needed to generate valid data. Following the record example, you can implement `transform/base:RDMRecordEntry`. Note that implementing this interface will produce valid _data_ for a record, however, the _metadata_ is not interfaced (It is an open question how much we should define this and avoid duplicating already existing Marshmallow schemas).

At this point you might be wondering "Why not Marshmallow then?". The answer is "separation of responsibilities, performance and simplicity". The later lays with the fact that most of the data transformation is custom, so we would end up with a schema full of `Method` fields, which does not differ much from what we have but would have an impact on performance (Marshmallow is slow...). Regarding the responsibilities part, validating - mostly referential, like vocabularies - can only be done on _load_ where RDM instance knowledge/appctx is available.

Note: there is an open question regarding a "soft/structural validation" step on the transformation. Right now this is forced because we access the fields with `[]` instead of allowing them not to be present like `.get(...)`.

### Load

The final step to have the records available in the RDM instance is to load them. The available `load/postgresql:PostgreSQLCopyLoad` will carry out 2 steps:

- 1. Prepare the inserts in one csv file per table.

```bash
$ /migration/data/tablestables1668697280.943311
    |
    | - pidstore_pid.csv
    | - rdm_parents_metadata.csv
    | - rdm_records_metadata.csv
    | - rdm_versions_state.csv
```

2. Perform the actual loading, using `COPY`. Doing all rows at once is more efficient than performing one `INSERT` per row.

Internally what is happening is that the `prepare` function makes use of `TableLoad` implementations and then yields the list of csv files. So the `load` only iterates through the filenames, not the actual entries.

A `TableLoad` is an abstraction that for every entry will yield one or more "row" entries. For example for a record it will yield: record recid, DOI and OAI (PersistentIdentifiers), record and parent metadata, etc.

## Notes

**Infrastructure**

While now we are simply running one after the other in the `run.py`, the idea is that all three steps will pull/push to/from queues so they can be deployed in different parts of the system (e.g. the load part in the worker nodes).

**Code**
Take into account that the code inside the `/migration` folder is placed under `zenodo-rdm` temporarily. Therefore, you can simply have:

- Your InvenioRDM instance running
- Execute code inside this folder as if it was any other pure Python package. The Invenio dependencies do not require an app context (e.g. db models)

There is an open discussion on where to place this code.

**Others**

- Using generators instead of lists, allows us to iterate through the data only once and perform the E-T-L steps on them. Instead of loop for E, loop for T, loop for L. In addition, this allows us to have the csv files open during the writing and closing them at the end (open/close is an expensive op when done 3M times).
- Naming is far from ideal, open to suggestions (e.g. ETL vs Stream, Load vs Stream - then TableLoad would be TableStream).
