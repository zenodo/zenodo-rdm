"""Dataclasses for generating table rows."""

from dataclasses import InitVar, dataclass


@dataclass
class PersistentIdentifier:

    id: str
    pid_type: str
    pid_value: str
    status: str
    object_type: str
    object_uuid: str
    created: str
    updated: str

    _table_name: InitVar[str] = "pidstore_pid"


@dataclass
class RDMRecordMetadata:

    id: str
    json: dict
    created: str
    updated: str
    version_id: int
    index: int
    bucket_id: str
    parent_id: str

    _table_name: InitVar[str] = "rdm_records_metadata"


@dataclass
class RDMRecordFile:

    id: str
    json: dict
    created: str
    updated: str
    version_id: int
    key: str
    record_id: str
    object_version_id: str

    _table_name: InitVar[str] = "rdm_records_files"


@dataclass
class RDMParentMetadata:

    id: str
    json: dict
    created: str
    updated: str
    version_id: int

    _table_name: InitVar[str] = "rdm_parents_metadata"


@dataclass
class RDMVersionState:

    latest_index: int
    parent_id: str
    latest_id: str
    next_draft_id: str

    _table_name: InitVar[str] = "rdm_versions_state"


@dataclass
class RDMDraftMetadata:

    id: str
    json: dict
    created: str
    updated: str
    version_id: int
    index: int
    bucket_id: str
    parent_id: str

    expires_at: str
    fork_version_id: int

    _table_name: InitVar[str] = "rdm_drafts_metadata"


@dataclass
class RDMDraftFile(RDMRecordFile):

    _table_name: InitVar[str] = "rdm_drafts_files"


@dataclass
class RDMParentCommunity:

    community_id: str
    record_id: str
    request_id: str

    _table_name: InitVar[str] = "rdm_parents_community"
