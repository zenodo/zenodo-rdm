# SPDX-FileCopyrightText: 2024-2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Base contract for ZenodoRDM moderation rules.

A rule is a callable returning a ``RuleResult`` that holds the typed ``Reason``
objects explaining how its score was reached. Reasons are narrated even when
they score zero, so a rule expected to fire but that didn't can still be
inspected. All types serialize cleanly via ``dataclasses.asdict``.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Reason:
    """A single scored observation made by a rule."""

    score: float
    label: str


@dataclass(frozen=True)
class RuleResult:
    """Outcome of a rule: its reasons and the derived total score."""

    reasons: list[Reason]
    score: float = field(init=False)

    def __post_init__(self):
        """Derive the total score from the reasons."""
        object.__setattr__(self, "score", sum(r.score for r in self.reasons))


class Rule:
    """Base class for moderation scoring rules."""

    def __call__(self, identity, draft=None, record=None) -> RuleResult:
        """Resolve the draft/record and delegate to ``evaluate``."""
        return self.evaluate(identity, record if record is not None else draft)

    def evaluate(self, identity, record) -> RuleResult:
        """Score the given record (or draft); implemented by each rule."""
        raise NotImplementedError
