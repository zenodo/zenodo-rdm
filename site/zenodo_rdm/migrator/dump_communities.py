import yaml
from pathlib import Path
from invenio_communities.communities.records.models import CommunityMetadata
community_map = {comm.slug: str(comm.id) for comm in CommunityMetadata.query.all()}
streams_path = str(Path('site/zenodo_rdm/migrator/streams.yaml').absolute())
streams = {}
with open(streams_path, 'r') as fp:
    streams = yaml.safe_load(fp)
streams["records"]["load"]["communities_cache"] = community_map
with open(streams_path, 'w') as fp:
    yaml.safe_dump(streams, fp, default_flow_style=False)
