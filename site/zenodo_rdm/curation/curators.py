# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Curators for ZenodoRDM Curation."""

from flask import current_app
from invenio_access.permissions import system_identity
from invenio_rdm_records.proxies import current_record_communities_service
from invenio_records_resources.services.uow import UnitOfWork

from zenodo_rdm.curation.proxies import current_curation


class BaseCurator:
    """Base Curator class."""

    def __init__(self, dry=False):
        """Constructor."""
        self.dry = dry

    def _evaluator(self, results):
        """Evaluates final result for based on results dict."""
        raise NotImplementedError()

    @property
    def rules(self):
        """Get rules to run."""
        raise NotImplementedError()

    def run(self, record, raise_rule_exc=False):
        """Run rules for the curator and evaluate result."""
        rule_results = {}
        for name, rule in self.rules.items():
            try:
                rule_results[name] = rule(record)
            except Exception as e:
                if raise_rule_exc:
                    raise e
                rule_results[name] = None

        evaluation = self._evaluator(rule_results)
        result = {"evaluation": evaluation, "rules": rule_results}
        self._post_run(record, result)
        return result

    def _post_run(self, record, result):
        """Actions to take after calculating rules."""
        pass


class EURecordCurator(BaseCurator):
    """Curator to check records for EC community."""

    def _evaluator(self, results):
        """Evaluate result for EC curation."""
        score = 0
        for rule, result in results.items():
            rule_score = current_curation.scores.get(rule)
            if result is None:
                continue
            elif type(rule_score) is int:
                score += rule_score if result else 0
            elif isinstance(rule_score, bool):
                if result:
                    return rule_score
                else:
                    continue
            else:
                raise ValueError("Unsupported score type configured.")
        return score >= current_curation.thresholds.get("EU_RECORDS_CURATION")

    @property
    def rules(self):
        """Get rules to run from config."""
        return current_app.config.get("CURATION_EU_RULES", {})

    def _post_run(self, record, result):
        """Actions to take after run."""
        if self.dry:
            current_app.logger.error(
                "Evaluation for EU record curator",
                extra={"record_id": record.pid.pid_value, "result": result},
            )
            return
        if result["evaluation"]:
            with UnitOfWork() as uow:
                current_record_communities_service.bulk_add(
                    system_identity,
                    current_app.config.get("EU_COMMUNITY_UUID"),
                    [record.pid.pid_value],
                    uow=uow,
                )
                uow.commit()
