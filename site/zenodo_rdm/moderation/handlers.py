from flask import current_app
from invenio_access.permissions import system_identity


class BaseScoreHandler:
    def __init__(self, app=None, rules=None):
        self.app = app
        self.rules = rules

    def run(self, identity, draft=None, record=None):
        score = 0
        rules = current_app.config[self.rules]
        for rule in rules:
            score += rule(identity, draft=draft, record=record)
            breakpoint()

        current_app.logger.warning(f"Moderation score for record({record.metadata['title']}): {score}")


class RecordScoreHandler(BaseScoreHandler):
    def __init__(self, app=None):
        super().__init__(app, rules="RDM_RECORD_MODERATION_SCORE_RULES")


class CommunityScoreHandler(BaseScoreHandler):
    def __init__(self, app=None):
        super().__init__(app, rules="COMMUNITY_MODERATION_SCORE_RULES")
