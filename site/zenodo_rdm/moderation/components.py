from flask import current_app
from invenio_drafts_resources.services.records.components import ServiceComponent


class RecordContentModerationComponent(ServiceComponent):
    """Service component for content moderation."""

    def publish(self, identity, draft=None, record=None):
        if current_app.config["RDM_USER_MODERATION_ENABLED"]:
            handlers = current_app.config["RDM_RECORD_MODERATION_HANDLERS"]
            for handler in handlers:
                handler.run(identity, draft, record)


class CommunityContentModerationComponent(ServiceComponent):
    """Service component for content moderation."""

    def create(self, identity, data=None, record=None, **kwargs):
        if current_app.config["RDM_USER_MODERATION_ENABLED"]:
            handlers = current_app.config["COMMUNITY_MODERATION_HANDLERS"]
            for handler in handlers:
                handler.run(identity, data, record)

    def update(self, identity, data=None, record=None, **kwargs):
        if current_app.config["RDM_USER_MODERATION_ENABLED"]:
            handlers = current_app.config["COMMUNITY_MODERATION_HANDLERS"]
            for handler in handlers:
                handler.run(identity, data, record)
