from abc import ABC, abstractmethod


class Transform(ABC):
    """Base class for data transformation."""

    @abstractmethod
    def run(self):
        """Transform and yield one element at a time."""
        pass


class Entry(ABC):
    """Base entry class."""

    def transform(self, entry):
        """Transform entry."""
        pass


class RDMRecordTransform(Transform):
    """Base class for data transformation."""

    @abstractmethod
    def _parent(self, entry):
        """Transform the parent record."""
        pass

    @abstractmethod
    def _record(self, entry):
        """Transform the record."""
        pass

    @abstractmethod
    def _draft(self, entry):
        """Transform the draft."""
        pass

    @abstractmethod
    def _record_files(self, entry):
        """Transform the record files."""
        pass

    @abstractmethod
    def _draft_files(self, entry):
        """Transform the draft files."""
        pass

    def _transform(self, entry):
        """Transform a single entry."""
        # the functions receive the full record/data entry
        # while in most cases the full view is not needed
        # since this is a low level tool used only by users
        # with deep system knowledge providing the flexibility
        # is future proofing and simplifying the interface
        return {
            "record": self._record(entry),
            "draft": self._draft(entry),
            "parent": self._parent(entry),
            "record_files": self._record_files(entry),
            "draft_files": self._draft_files(entry),
        }

    def run(self, datagen):
        """Transform and yield one element at a time."""
        for entry in datagen:
            yield self._transform(entry)


class RDMRecordEntry(Entry):
    """Transform a single record entry."""

    @abstractmethod
    def _created(self, entry):
        """Returns the creation date of the record."""
        pass

    @abstractmethod
    def _updated(self, entry):
        """Returns the update date of the record."""
        pass

    @abstractmethod
    def _version_id(self, entry):
        """Returns the version id of the record."""
        pass

    @abstractmethod
    def _index(self, entry):
        """Returns the index of the record."""
        pass

    @abstractmethod
    def _recid(self, entry):
        """Returns the recid of the record."""
        pass

    @abstractmethod
    def _pids(self, entry):
        """Returns the pids of the record."""
        pass

    @abstractmethod
    def _files (self, entry):
        """Transform the files of a record."""
        pass

    @abstractmethod
    def _access(self, entry):
        """Transform the access of a record."""
        pass

    @abstractmethod
    def _metadata(self, entry):
        """Transform the metadata of a record.

        No schema/dictionary is enforced as choice balanced between
        duplicating the schema with abstract methods and allowing for flexibility
        i.e. different metadata schema.
        """
        pass

    def transform(self, entry):
        """Transform a record single entry."""

        return {
            "created": self._created(entry),
            "updated": self._updated(entry),
            "version_id": self._version_id(entry),
            "index": self._index(entry),
            "json": {
                "id": self._recid(entry),
                "pids": self._pids(entry),
                "files": self._files(entry),
                "metadata": self._metadata(entry),
                "access": self._access(entry),
            },
        }
