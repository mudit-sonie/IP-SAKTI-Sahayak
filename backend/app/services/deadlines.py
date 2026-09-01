"""Derived statutory deadlines (roadmap S9).

Given one anchor date the user supplies (a filing date, a priority date, …),
compute the standard statutory windows that run off it. Rule-driven, not an LLM;
each rule grounds to a real provision where the corpus supports it.

These are indicative schedules to plan around — extensions, condonation of
delay, and the exact reckoning (priority vs. filing) are matter-specific and
must be confirmed with the official rules.
"""
from __future__ import annotations

import calendar
from dataclasses import dataclass, field
from datetime import date

from app.core.logging import get_logger
from app.schemas import Citation, Deadline, DeadlineAnchor
from app.services.checklist import _ground
from app.store.repos import new_id

logger = get_logger(__name__)


def _add_months(d: date, months: int) -> date:
    total = d.month - 1 + months
    year = d.year + total // 12
    month = total % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


@dataclass(frozen=True)
class _Rule:
    key: str
    title: str
    months: int
    detail: str
    probe: str | None = None
    jurisdictions: tuple[str, ...] = ("india",)


_RULES: dict[DeadlineAnchor, list[_Rule]] = {
    DeadlineAnchor.patent_filing: [
        _Rule(
            "patent_rfe",
            "File the request for examination",
            48,
            "A request for examination must be filed within 48 months of the "
            "priority date or filing date, whichever is earlier.",
            probe="request for examination time limit forty eight months patent",
        ),
        _Rule(
            "patent_first_renewal",
            "First renewal (annuity) fee falls due",
            24,
            "Renewal fees are payable before the expiration of the second year "
            "and for every year thereafter to keep the patent in force.",
            probe="renewal fees patent payable expiration second year",
        ),
        _Rule(
            "patent_term_expiry",
            "Patent term expires (20 years)",
            240,
            "The term of every patent is 20 years from the date of filing of the "
            "application.",
            probe="term of every patent twenty years from date of filing",
        ),
    ],
    DeadlineAnchor.patent_priority: [
        _Rule(
            "patent_convention",
            "Convention / Paris route filing deadline (12 months)",
            12,
            "A convention application claiming priority must be filed within 12 "
            "months of the earliest priority date.",
            probe="convention application priority period twelve months patent",
        ),
        _Rule(
            "patent_pct_national_phase",
            "PCT national phase entry (31 months)",
            31,
            "National phase entry from an international (PCT) application is "
            "generally due at 31 months from the priority date in India.",
            probe="national phase international application thirty one months",
        ),
    ],
    DeadlineAnchor.tm_application: [
        _Rule(
            "tm_exam_reply",
            "Reply to the examination report",
            1,
            "A response to the examination report is due within one month of its "
            "receipt (extensions may be available).",
            probe="reply examination report trade mark one month time",
        ),
        _Rule(
            "tm_renewal",
            "Trade mark renewal (10 years)",
            120,
            "Registration is for 10 years and is renewable for further 10-year "
            "periods.",
            probe="renewal registration trade mark ten years period",
        ),
    ],
    DeadlineAnchor.gi_application: [
        _Rule(
            "gi_renewal",
            "GI registration renewal (10 years)",
            120,
            "Registration of a geographical indication is for 10 years and may "
            "be renewed for further periods of 10 years.",
            probe="registration geographical indication ten years renewal period",
        ),
    ],
}


@dataclass
class Derivation:
    deadlines: list[Deadline] = field(default_factory=list)


def anchor_label(anchor: DeadlineAnchor) -> str:
    return {
        DeadlineAnchor.patent_filing: "patent filing date",
        DeadlineAnchor.patent_priority: "patent priority date",
        DeadlineAnchor.tm_application: "trade mark application date",
        DeadlineAnchor.gi_application: "GI application date",
    }[anchor]


def parse_date(value: str) -> date:
    return date.fromisoformat(value.strip())


def derive(
    anchor: DeadlineAnchor,
    anchor_date: date,
    jurisdiction: str,
    *,
    done_by_rule: dict[str, bool] | None = None,
) -> list[Deadline]:
    done_by_rule = done_by_rule or {}
    out: list[Deadline] = []
    for rule in _RULES.get(anchor, []):
        if jurisdiction not in rule.jurisdictions:
            continue
        due = _add_months(anchor_date, rule.months)
        cites: list[Citation] = _ground(rule.probe, jurisdiction) if rule.probe else []
        out.append(
            Deadline(
                id=new_id("dl_"),
                title=rule.title,
                due_date=due.isoformat(),
                kind="derived",
                detail=(
                    f"{rule.detail} Computed as {anchor_label(anchor)} "
                    f"({anchor_date.isoformat()}) + {rule.months} months."
                ),
                done=done_by_rule.get(rule.key, False),
                source_rule=rule.key,
                anchor=anchor.value,
                citations=cites,
            )
        )
    return out
