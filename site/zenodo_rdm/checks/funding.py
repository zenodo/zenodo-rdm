from dataclasses import asdict, dataclass, field

from invenio_checks.base import Check
from invenio_checks.models import CheckConfig
from invenio_records_resources.proxies import current_service_registry
from invenio_access.permissions import system_identity

# from zenodo_rdm.orcha import OrchaClient

@dataclass
class CheckResult:
    """Result of a check."""

    id: str
    title: str
    message: str
    description: str
    errors: list[dict] = field(default_factory=list)
    sync: bool = True
    success: bool = True

    def to_dict(self):
        return asdict(self)

class FundingCheck(Check):
    """Check for record and award relevance with each other."""
    id = "funding"
    title = "Funding check"
    description = "Validates record funding metadata against configured rules."
    sort_order = 30

    def _get_award_description(self, funding):
        """Fast safe extraction of award description."""
        if not funding:
            return None

        award_id = (funding[0].get("award") or {}).get("id")
        if not award_id:
            return None

        try:
            awards_service = current_service_registry.get("awards")
            award = awards_service.read(system_identity, award_id)

            return (
                award.to_dict()
                .get("description", {})
                .get("en")
            )
        except Exception:
            return None

    def run(self, record, config: CheckConfig):
        metadata = record.get("metadata") or {}
        funding = metadata.get("funding") or []

        rule = (config.params.get("rules") or [{}])[0]

        message = rule.get("message")
        description = rule.get("description")
        title = rule.get("title", self.title)

        result = CheckResult(
            id=self.id,
            title=title,
            message=message,
            description=description,
            errors=[],
            success=True,
        )

        award_description = self._get_award_description(funding)

        try:
            # The OrchaClient and workflow triggering is commented out as it requires the 
            # actual Orcha service and workflow to be set up. 
            # The response from Orcha should be a dictionary
            # with at least a "match" key indicating if the funding metadata matches the rules, and optionally a "message" key for any error message.
            
            
            # client = OrchaClient(
            #     base_url=config.params.get("orcha_url"),
            #     key_path=config.params.get("key_path"),
            #     tenant=config.params.get("tenant"),
            # )

            # response = client.trigger_workflow(
            #     payload={
            #         "metadata": metadata,
            #         "award_description": award_description,
            #         "rule": rule,
            #     },
            #     token=config.params.get("token"),
            # )
            response = {}

            if not response.get("match", True):
                result.errors.append({
                    "field": "metadata.funding",
                    "messages": [response.get("message", message)],
                    "description": description,
                    "severity": config.severity.error_value,
                })
                result.success = False

        except Exception:
            result.errors.append({
                "field": "metadata.funding",
                "messages": ["Funding validation service unavailable."],
                "description": description,
                "severity": config.severity.warning_value,
            })
            result.success = False

        return result