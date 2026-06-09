# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 CERN.
#
# Zenodo RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Zenodo-specific subcommunity checks."""

from invenio_access.permissions import system_identity
from invenio_accounts.models import Domain, DomainStatus, User
from invenio_cache import current_cache
from invenio_checks.base import Check
from invenio_checks.contrib.metadata import ExpressionResult
from invenio_checks.contrib.metadata.check import CheckResult, MetadataCheck
from invenio_checks.contrib.metadata.rules import RuleResult
from invenio_communities.proxies import current_communities
from invenio_rdm_records.proxies import current_community_records_service


def _get_funding_per_community(community, funder_id):
    community.relations.dereference()
    if "funding" in community.metadata:
        funding = community.metadata["funding"]
        return {
            f["award"]["number"]: f["award"].get("acronym")
            for f in funding
            if "award" in f and "number" in f["award"]
               and f["funder"].get("id") == funder_id
        }
    return {}


class SubcommunityMetadataCheck(MetadataCheck):
    """Check for validating community metadata against configured rules."""

    id = "subcommunity_metadata"
    title = "Community metadata"
    description = "The following metadata was automatically suggested based on the selected EU project."
    sort_order = 34


class CommunityMembershipCheck(Check):
    """Check that at least one owner and one manager have a verified institutional email."""

    id = "subcommunity_member"
    title = "Member affiliation"
    description = ("Verifies that at least one community member (owner or manager) is affiliated with "
                   "one of the EU project’s participating organizations. ")
    sort_order = 31

    def run(self, record, config):
        """Run the check against the community's members."""
        result = CheckResult(self.id)

        verified_domains = self._get_verified_domains()

        Membership = current_communities.service.members.record_cls
        members = Membership.model_cls.query.filter(
            Membership.model_cls.community_id == str(record.id)
        ).all()

        user_ids = {int(m.user_id) for m in members if m.user_id is not None}
        users_by_id = {
            u.id: u
            for u in User.query.filter(User.id.in_(user_ids)).all()
        }
        users = []
        verified_users = 0
        unverified_users = 0
        for member in (m for m in members if m.role in ("manager", "owner")):
            user = users_by_id[int(member.user_id)]
            verified = user.domain in verified_domains
            user_data = {"domain": user.domain, "role": member.role.capitalize(), "verified": verified}
            if user_name := user.user_profile.get('full_name') or user.username:
                user_data.update({"name": user_name})
            users.append(user_data)

            if verified:
                verified_users += 1
            else:
                unverified_users += 1
        if verified_users == 0 and unverified_users != 0:
            description = "At least one community member should have a verified email."
        else:
            description = "The community has at least one member who is verified."
        rule_result = RuleResult(
            rule_id="membership:verified",
            rule_title="Verified community member",
            rule_message="Verified community member",
            rule_description=description,
            level=config.severity.error_value,
            success=bool(verified_users),
            check_results=[ExpressionResult(success=bool(verified_users), value=users)],
        )
        result.add_rule_result(rule_result)
        if not verified_users:
            result.add_errors([
                {
                    "field": "members.verified",
                    "messages": [rule_result.rule_message],
                    "description": rule_result.rule_description,
                    "severity": rule_result.level,
                }
            ])

        return result

    def _get_verified_domains(self):
        """Return the set of verified institutional domains, cached for 1 hour."""
        cache_key = "checks:verified_domains"
        domains = current_cache.get(cache_key)
        if not domains:
            domains = {
                d.domain
                for d in Domain.query.filter(
                    Domain.status == DomainStatus.verified
                ).all()
            }
            current_cache.set(cache_key, domains, timeout=3600)
        return domains


class SubcommunityValidationCheck(Check):
    """Check project validation for EU subcommunity membership."""

    id = "subcommunity_validation"
    title = "Project validation"
    description = "Validates the EU project grant and checks for duplicate communities."
    sort_order = 32

    def run(self, record, config):
        """Run eligibility checks against the subcommunity."""
        result = CheckResult(self.id)
        # decide how to do this, add a config? hardcode?
        ec_funder_id = config.params.get("ec_funder_id", "00k4n6c32")
        eu_community_id = str(config.community_id)
        funding_data = _get_funding_per_community(record, ec_funder_id)
        # Build a formatted list that can be used to display grant number and acronym
        funding = [
            f"Grant {number} ({acronym})" if acronym else f"Grant {number}"
            for number, acronym in funding_data.items()
        ]

        for rule_result in [
            self._check_has_ec_funding(record, funding, config),
            self._check_no_duplicate_grant(record, ec_funder_id, funding, config),
        ]:
            result.add_rule_result(rule_result)
            if not rule_result.success:
                result.add_errors([{
                    "field": rule_result.rule_id,
                    "messages": [rule_result.rule_message],
                    "description": rule_result.rule_description,
                    "severity": rule_result.level,
                }])

        return result

    def _check_has_ec_funding(self, record, funding, config):
        """Check the community has at least one EC funding entry."""
        record.relations.dereference()
        success = bool(funding)
        return RuleResult(
            rule_id="eligibility:ec_funding",
            rule_title="Community must have at least one grant",
            rule_message="Funding information on the community",
            rule_description=(
                "No funding information found on this community."
                if not success else
                f"This community has funding: {', '.join(funding)}."
            ),
            level=config.severity.error_value,
            success=success,
            check_results=[],
        )

    def _check_no_duplicate_grant(self, record, ec_funder_id, funding, config):
        """Check no existing EU subcommunity has the same EC grant."""
        duplicates = set()
        for num in funding:
            results = current_communities.service.search(
                system_identity,
                params={
                    "q": (
                        f'metadata.funding.award.id:"{num}"'
                        f" AND metadata.funding.funder.id:{ec_funder_id}"
                    ),
                    "size": 10,
                },
            )
            if any((h["id"] != str(record.id) for h in results.hits)):
                duplicates.add(num)

        success = not duplicates
        if success:
            description = "There is no existing community registered for this grant number in the EU Open Research Repository."
        else:
            description = f"Duplicate communities were found for {', '.join(funding)}."
        return RuleResult(
            rule_id="eligibility:no_duplicate_grant",
            rule_title="A community with the same grant already exists",
            rule_message="No existing community for this project",
            rule_description=description,
            level=config.severity.error_value,
            success=success,
            check_results=[],
        )


class SubcommunityRecordCheck(Check):
    """Check that records in the community have the required metadata."""

    id = "subcommunity_record_metadata"
    title = "Record metadata"
    description = "All records in the community must include the EU project's funding information in their metadata."
    sort_order = 33

    def run(self, record, config):
        """Run the check against the community's records."""
        result = CheckResult(self.id)
        community_id = str(record.id)
        ec_funder_id = config.params.get("ec_funder_id", "00k4n6c32")
        community_funding = _get_funding_per_community(record, ec_funder_id)

        total = current_community_records_service.search(
            system_identity,
            community_id=community_id,
        ).total

        unfunded = current_community_records_service.search(
            system_identity,
            community_id=community_id,
            params={"q": "NOT _exists_:metadata.funding"},
        ).total

        rules = [self._check_unfunded_records(unfunded, total, config)]
        if unfunded != total:
            rules.append(self._check_mismatched_records(community_id, total, config, ec_funder_id, community_funding))
        for rule_result in rules:
            result.add_rule_result(rule_result)
            if not rule_result.success:
                result.add_errors([{
                    "field": rule_result.rule_id,
                    "messages": [rule_result.rule_message],
                    "description": rule_result.rule_description,
                    "severity": rule_result.level,
                }])

        return result

    def _check_unfunded_records(self, unfunded, total, config):
        """Check how many records are missing funding metadata entirely."""
        success = unfunded == 0
        if success:
            if total == 0:
                description = f"No records in this community yet."
            else:
                description = "All records in this community have project funding."
        else:
            description = f"""
                {unfunded} of {str(total) + (' records' if total > 1 else ' record')} in this community 
                {'do' if unfunded > 1 else 'does'} not have EU project funding in their metadata. 
                Records must include funding information to be part of the EU Open Research Repository.
            """
        return RuleResult(
            rule_id="records:funding_metadata",
            rule_title="Records have funding metadata",
            rule_message="All records must have funding information",
            rule_description=description,
            level=config.severity.error_value,
            success=success,
            check_results=[ExpressionResult(success=success, value=str({"unfunded": unfunded, "total": total}))],
        )

    def _check_mismatched_records(self, community_id, total, config, ec_funder_id, community_funding):
        """Check how many records have EC funding that doesn't match the community's grants."""
        if not community_funding:
            return RuleResult(
                rule_id="records:funding_mismatch",
                rule_title="Records have matching grant",
                rule_message="Records must be funded by the community's EC grant",
                rule_description="No EC grants found on this community to match against.",
                level=config.severity.error_value,
                success=False,
                check_results=[],
            )

        award_clauses = " OR ".join(
            f'metadata.funding.award.number:"{n}"' for n in community_funding.keys()
        )
        mismatched = current_community_records_service.search(
            system_identity,
            community_id=community_id,
            params={
                "q": f"metadata.funding.funder.id:{ec_funder_id} AND NOT ({award_clauses})",
            },
        ).total

        success = mismatched == 0
        if success:
            if total == 0:
                description = f"No records in this community yet."
            else:
                description = f"All records in this community are funded by the community's EC grant."
        else:
            description = f"""
                {mismatched} of {str(total) + (' records' if total > 1 else ' record')} records in this community
                have a grant that {'do' if mismatched > 1 else 'does'} not match
                {"" if len(community_funding) == 1 else "any of "} the EU project funding of the community
                (Grant {', Grant '.join(community_funding.keys())}).
            """
        return RuleResult(
            rule_id="records:funding_mismatch",
            rule_title="Records have matching grant",
            rule_message="Records must be funded by the community's EC grant",
            rule_description=description,
            level=config.severity.error_value,
            success=success,
            check_results=[ExpressionResult(success=success, value=str({"mismatched": mismatched, "total": total}))],
        )
