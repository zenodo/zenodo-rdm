# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 CERN.
#
# Zenodo RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Zenodo-specific subcommunity checks."""

from urllib.parse import urlparse

from invenio_access.permissions import system_identity
from invenio_accounts.models import Domain, DomainStatus, User
from invenio_cache import current_cache
from invenio_checks.base import Check
from invenio_checks.contrib.metadata import ExpressionResult
from invenio_checks.contrib.metadata.check import MetadataCheck, MetadataCheckResult
from invenio_checks.contrib.metadata.rules import RuleResult
from invenio_communities.proxies import current_communities
from invenio_db import db
from invenio_rdm_records.proxies import current_community_records_service
from invenio_records_resources.proxies import current_service_registry
from invenio_vocabularies.contrib.affiliations.api import Affiliation
from invenio_vocabularies.contrib.awards.api import Award


def _get_funding_per_community(community, funder_id):
    community.relations.dereference()
    if "funding" in community.metadata:
        funding = community.metadata["funding"]
        return {
            f["award"]["number"]: f["award"].get("acronym")
            for f in funding
            if "award" in f
            and "number" in f["award"]
            and f["funder"].get("id") == funder_id
        }
    return {}


class SubcommunityMetadataCheck(MetadataCheck):
    """Check for validating community metadata against configured rules."""

    id = "subcommunity_metadata"
    title = "Community metadata"
    description = "The following metadata was automatically suggested based on the selected EU project."
    sort_order = 34

    def run(self, record, config, deleted_member_id=None):
        """Validate community metadata against the selected EU project award."""
        result = super().run(record, config)
        ec_funder_id = config.params.get("ec_funder_id", "00k4n6c32")

        funding = next(
            (
                f
                for f in record.metadata.get("funding", [])
                if f.get("funder", {}).get("id") == ec_funder_id
            ),
            None,
        )

        if not funding:
            return result

        award_id = funding.get("award", {}).get("id")
        if not award_id:
            return result

        award = Award.pid.resolve(award_id)
        if not award:
            return result

        award_orgs = award.get("organizations", [])
        community_orgs = record.metadata.get("organizations", [])

        def normalize_name(name):
            return name.strip().lower() if name else None

        # Match organizations by either identifier or normalized name
        award_ids = {org["id"] for org in award_orgs if org.get("id")}

        award_names = {
            normalize_name(org.get("name")) for org in award_orgs if org.get("name")
        }

        matching_orgs = [
            org
            for org in community_orgs
            if (
                org.get("id") in award_ids
                or normalize_name(org.get("name")) in award_names
            )
        ]

        for rule in result.rule_results:
            if rule.rule_id != "metadata:organizations":
                continue

            if matching_orgs:
                if rule.check_results:
                    rule.check_results[0].value = matching_orgs
            else:
                rule.success = False
                rule.level = "warning"
                rule.rule_description = (
                    "The community organizations should contain at least one "
                    "organization defined in the project award."
                )

            break

        return result


class CommunityMembershipCheck(Check):
    """
    Check that community members have affiliations.

    Checks that at least one community member (owner or manager) has a verified domain
    or is affiliated (via their email domain) with a recognized award organization.
    """

    id = "subcommunity_member"
    title = "Member affiliation"
    description = (
        "Verifies that at least one community member (owner or manager) is affiliated with "
        "one of the EU project’s participating organizations."
    )
    sort_order = 31
    allow_rerun = True

    def run(self, record, config, deleted_member_id=None):
        """Run the check against the community's members, excluding members being removed."""
        result = MetadataCheckResult(self.id, self.title, self.description)
        verified_domains = self._get_verified_domains()
        ec_funder_id = config.params.get("ec_funder_id", "00k4n6c32")
        award_org_data = self._get_award_org_data(record, ec_funder_id)

        Membership = current_communities.service.members.record_cls

        # Fetch active manager/owner members and their associated User models in a single query
        query = (
            db.session.query(Membership.model_cls, User)
            .join(User, Membership.model_cls.user_id == User.id)
            .filter(
                Membership.model_cls.community_id == str(record.id),
                Membership.model_cls.active.is_(True),
                Membership.model_cls.role.in_(["manager", "owner"]),
            )
        )

        valid_users = []
        invalid_users = []

        for member, user in query.all():
            # Exclude member currently being removed
            if str(member.user_id) == str(deleted_member_id):
                continue

            user_domain = self._normalize_domain(user.domain)
            verified = user_domain in verified_domains if user_domain else False
            affiliated_to = self.is_affiliated_to(user_domain, award_org_data)

            user_name = (
                user.user_profile.get("full_name") or user.username
                if user.user_profile
                else user.username
            )

            user_data = {
                "name": user_name,
                "domain": user.domain,
                "role": member.role.capitalize(),
                "verified": verified,
                "affiliation": affiliated_to,
            }

            if affiliated_to:
                user_data["level"] = "success"
                valid_users.append(user_data)
            elif verified:
                user_data["level"] = "info"
                valid_users.append(user_data)
            else:
                user_data["level"] = "warning"
                invalid_users.append(user_data)

        success = len(valid_users) > 0

        if success:
            users = valid_users
            level = "info"
            description = (
                "The community has at least one owner or manager "
                "with a verified domain or affiliation to one of the "
                "award's organizations."
            )
        else:
            users = invalid_users
            level = "error"
            description = (
                "None of the community owners or managers are verified "
                "or affiliated with one of the award's organizations."
            )

        rule_result = RuleResult(
            rule_id="membership:verified",
            rule_title="Verified community member",
            rule_message="Verified community member",
            rule_description=description,
            level=level,
            success=success,
            check_results=[
                ExpressionResult(
                    success=success,
                    value=users,
                )
            ],
        )

        result.add_rule_result(rule_result)

        if not success:
            result.add_errors(
                [
                    {
                        "field": "members.verified",
                        "messages": [rule_result.rule_message],
                        "description": rule_result.rule_description,
                        "severity": rule_result.level,
                    }
                ]
            )

        return result

    def _normalize_domain(self, value):
        """Normalize domain names and URLs."""
        if not value:
            return None

        value = value.lower().strip()

        if value.startswith(("http://", "https://")):
            value = urlparse(value).hostname or ""

        value = value.removeprefix("www.")
        return value if value else None

    def _get_verified_domains(self):
        """Return cached set of verified institutional domains."""
        cache_key = "checks:verified_domains"
        domains = current_cache.get(cache_key)

        if domains is None:
            raw_domains = Domain.query.filter(
                Domain.status == DomainStatus.verified
            ).all()
            domains = {
                norm_domain
                for domain in raw_domains
                if (norm_domain := self._normalize_domain(domain.domain))
            }
            current_cache.set(cache_key, domains, timeout=3600)

        return domains

    def _get_award_org_data(self, record, funder_id):
        """Return organizations and their matchable domains extracted from ROR records."""
        organizations = []

        for funding in record.metadata.get("funding", []):
            if funding.get("funder", {}).get("id") != funder_id:
                continue

            award_id = funding.get("award", {}).get("id")
            if not award_id:
                continue

            try:
                award = Award.pid.resolve(award_id)
            except Exception:
                continue

            if not award:
                continue

            for organization in award.get("organizations", []):
                domains = set()
                name = None

                ror_id = organization.get("id")

                if ror_id:
                    try:
                        affiliation = Affiliation.pid.resolve(ror_id)
                    except Exception:
                        continue

                    if not affiliation:
                        continue

                    name = affiliation.get("name")

                    for domain in affiliation.get("domains", []):
                        if norm := self._normalize_domain(domain):
                            domains.add(norm)

                    if website := affiliation.get("website"):
                        if norm := self._normalize_domain(website):
                            domains.add(norm)

                    for identifier in affiliation.get("identifiers", []):
                        if identifier.get("scheme") == "url":
                            if norm := self._normalize_domain(
                                identifier.get("identifier")
                            ):
                                domains.add(norm)
                else:
                    name = organization.get("organization") or organization.get("name")

                if name and domains:
                    organizations.append(
                        {
                            "name": name,
                            "domains": domains,
                        }
                    )

        return organizations

    def is_affiliated_to(self, user_domain, organizations):
        """
        Return organization name if user domain matches exact or subdomain.

        Examples:
        - user@cern.ch -> matches cern.ch
        - user@sub.cern.ch -> matches cern.ch
        """
        user_domain = self._normalize_domain(user_domain)
        if not user_domain:
            return None

        for organization in organizations:
            for domain in organization["domains"]:
                if user_domain == domain or user_domain.endswith(f".{domain}"):
                    return organization["name"]

        return None


class SubcommunityValidationCheck(Check):
    """Check project validation for EU subcommunity membership."""

    id = "subcommunity_validation"
    title = "Project validation"
    description = "Validates the EU project grant and checks for duplicate communities."
    sort_order = 32

    def run(self, record, config):
        """Run eligibility checks against the subcommunity."""
        result = MetadataCheckResult(self.id, self.title, self.description)
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
                result.add_errors(
                    [
                        {
                            "field": rule_result.rule_id,
                            "messages": [rule_result.rule_message],
                            "description": rule_result.rule_description,
                            "severity": rule_result.level,
                        }
                    ]
                )

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
                if not success
                else f"This community has funding: {', '.join(funding)}."
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
    target_type = "community"
    sync = False
    allow_rerun = True

    def run(self, record, config):
        """Run the check against the community's records."""
        result = MetadataCheckResult(self.id, self.title, self.description)
        community_id = str(record.id)
        ec_funder_id = config.params.get("ec_funder_id", "00k4n6c32")
        community_funding = _get_funding_per_community(record, ec_funder_id)
        total = current_community_records_service.search(
            system_identity,
            community_id=community_id,
        ).total
        rule = self._check_record_funding(
            community_id,
            total,
            config,
            ec_funder_id,
            community_funding,
        )

        result.add_rule_result(rule)

        if not rule.success:
            result.add_errors(
                [
                    {
                        "field": rule.rule_id,
                        "messages": [rule.rule_message],
                        "description": rule.rule_description,
                        "severity": rule.level,
                    }
                ]
            )

        return result

    def _check_record_funding(
        self, community_id, total, config, ec_funder_id, community_funding
    ):
        """Check that all records contain one of the community's EC grants."""
        if not community_funding:
            return RuleResult(
                rule_id="records:funding",
                rule_title="Records have community funding",
                rule_message="All records must include the community's funding information",
                rule_description="No EC grants found on this community to match against.",
                level=config.severity.error_value,
                success=False,
                check_results=[],
            )

        grant_id, grant_title = next(iter(community_funding.items()))
        award_clauses = " OR ".join(
            f'metadata.funding.award.number:"{grant}"' for grant in community_funding
        )

        non_compliant = current_community_records_service.search(
            system_identity,
            community_id=community_id,
            params={
                "q": (
                    f"NOT (metadata.funding.funder.id:{ec_funder_id} "
                    f"AND ({award_clauses}))"
                ),
            },
        ).total

        success = non_compliant == 0
        if total == 0:
            description = "No records in this community yet."
        elif success:
            description = "All records in this community include the community's EU project funding."
        else:
            grants = ", ".join(community_funding.keys())
            description = (
                f"{non_compliant} of {total} "
                f"{'records' if total != 1 else 'record'} "
                f"do not include the community's EU project funding "
                f"(GA {grants})."
            )

        return RuleResult(
            rule_id="records:funding",
            rule_title="Records have community funding",
            rule_message="All records must include the community's funding information",
            rule_description=description,
            level=config.severity.error_value,
            success=success,
            check_results=[
                ExpressionResult(
                    success=success,
                    value={
                        "unfunded": non_compliant,
                        "total": total,
                        "funding": {
                            "grant_id": grant_id,
                            "grant_title": grant_title,
                        },
                        "details": (
                            "Records in this community need to include "
                            f"the project {grant_title} (GA {grant_id}) "
                            "in their funding metadata before the community can "
                            "be included in the EU Open Research Repository."
                        ),
                    },
                )
            ],
        )
