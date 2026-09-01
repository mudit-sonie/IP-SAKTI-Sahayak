"""Patent & GI fee calculators (roadmap S11).

A small static rules table plus a calculator. The figures below are the official
e-filing amounts from the Patents Rules First Schedule and the GI Rules First
Schedule as of the stated `as_of` date. Government fees change by amendment —
treat every output as indicative and confirm against the current schedule
before relying on it. Correcting a number here is a one-line edit.
"""
from __future__ import annotations

from app.schemas import (
    FeeEntity,
    FeeEstimateLine,
    FeeEstimateRequest,
    FeeEstimateResponse,
    FeeItem,
    FeeRenewalBand,
    FeesResponse,
    FeeSchedule,
)

DISCLAIMER = (
    "Indicative statutory fees only, at e-filing rates. Government fees change by "
    "amendment and physical-filing rates are higher (typically +10%). Attorney / "
    "agent professional charges are not included. Confirm against the current "
    "First Schedule before filing."
)

_PATENT_ENTITIES = [
    FeeEntity(
        key="individual_startup_small",
        label="Natural person / startup / small entity / educational institution",
    ),
    FeeEntity(key="others", label="Other(s), incl. large entity"),
]

PATENT_SCHEDULE = FeeSchedule(
    track="patent",
    title="Patent fees (India, e-filing)",
    as_of="2024-04-01",
    source="The Patents Rules, 2003 — First Schedule",
    source_url="https://ipindia.gov.in/fee-1998.htm",
    entities=_PATENT_ENTITIES,
    items=[
        FeeItem(
            code="filing", label="Filing of application (Form 1)",
            category="Filing",
            amounts={"individual_startup_small": 1600, "others": 8000},
        ),
        FeeItem(
            code="early_publication",
            label="Request for early publication (Form 9)",
            category="Publication",
            amounts={"individual_startup_small": 2500, "others": 12500},
        ),
        FeeItem(
            code="rfe", label="Request for examination (Form 18)",
            category="Examination",
            amounts={"individual_startup_small": 4000, "others": 20000},
        ),
        FeeItem(
            code="expedited_rfe",
            label="Request for expedited examination (Form 18A)",
            category="Examination",
            amounts={"individual_startup_small": 8000, "others": 60000},
        ),
        FeeItem(
            code="extra_claims",
            label="Each claim in excess of 10 (per claim)",
            category="Excess",
            amounts={"individual_startup_small": 320, "others": 1600},
            note="Charged on the number over 10, at filing and again at RFE if increased.",
        ),
        FeeItem(
            code="extra_pages",
            label="Each page of specification in excess of 30 (per page)",
            category="Excess",
            amounts={"individual_startup_small": 160, "others": 800},
        ),
    ],
    renewal_bands=[
        FeeRenewalBand(from_year=3, to_year=6,
                       amounts={"individual_startup_small": 800, "others": 4000}),
        FeeRenewalBand(from_year=7, to_year=10,
                       amounts={"individual_startup_small": 2400, "others": 12000}),
        FeeRenewalBand(from_year=11, to_year=15,
                       amounts={"individual_startup_small": 4800, "others": 24000}),
        FeeRenewalBand(from_year=16, to_year=20,
                       amounts={"individual_startup_small": 8000, "others": 40000}),
    ],
    notes=[
        "Renewal fees are payable from the 3rd year; the term is 20 years from filing.",
        "A 10% surcharge applies to physical (non-electronic) filing.",
    ],
)

GI_SCHEDULE = FeeSchedule(
    track="gi",
    title="Geographical Indication fees (India)",
    as_of="2024-04-01",
    source="The Geographical Indications of Goods (Registration and Protection) "
    "Rules, 2002 — First Schedule",
    source_url="https://ipindia.gov.in/form-and-fees-gi.htm",
    entities=[FeeEntity(key="standard", label="Applicant")],
    items=[
        FeeItem(
            code="gi_application",
            label="Application to register a GI, one class (Form GI-1)",
            category="Registration",
            amounts={"standard": 5000},
        ),
        FeeItem(
            code="gi_application_extra_class",
            label="Application to register a GI, each additional class",
            category="Registration",
            amounts={"standard": 5000},
        ),
        FeeItem(
            code="gi_authorised_user",
            label="Application to register an authorised user (Form GI-3)",
            category="Authorised user",
            amounts={"standard": 500},
        ),
        FeeItem(
            code="gi_renewal",
            label="Renewal of registration (Form GI-4)",
            category="Renewal",
            amounts={"standard": 5000},
            note="Registration lasts 10 years and is renewable for further 10-year terms.",
        ),
    ],
    notes=["GI registration is for 10 years, renewable."],
)

_SCHEDULES = {"patent": PATENT_SCHEDULE, "gi": GI_SCHEDULE}


def get_schedules() -> FeesResponse:
    return FeesResponse(disclaimer=DISCLAIMER, schedules=list(_SCHEDULES.values()))


def estimate(req: FeeEstimateRequest) -> FeeEstimateResponse:
    sched = _SCHEDULES.get(req.track)
    if sched is None:
        raise ValueError(f"unknown track: {req.track}")
    if req.entity not in {e.key for e in sched.entities}:
        raise ValueError(f"unknown entity for {req.track}: {req.entity}")

    lines: list[FeeEstimateLine] = []
    by_code = {it.code: it for it in sched.items}
    for code in req.item_codes:
        item = by_code.get(code)
        if item is None:
            continue
        amount = item.amounts.get(req.entity)
        if amount is None:
            continue
        lines.append(FeeEstimateLine(code=code, label=item.label, amount=amount))

    if req.renewal_from_year and req.renewal_to_year and sched.renewal_bands:
        lo = max(req.renewal_from_year, 1)
        hi = req.renewal_to_year
        if hi >= lo:
            renewal_total = 0
            for band in sched.renewal_bands:
                per_year = band.amounts.get(req.entity)
                if per_year is None:
                    continue
                overlap = max(0, min(hi, band.to_year) - max(lo, band.from_year) + 1)
                renewal_total += overlap * per_year
            if renewal_total:
                lines.append(
                    FeeEstimateLine(
                        code="renewal",
                        label=f"Renewal fees, years {lo}–{hi}",
                        amount=renewal_total,
                        detail="Sum of per-year fees across the applicable bands.",
                    )
                )

    return FeeEstimateResponse(
        track=req.track,
        entity=req.entity,
        currency=sched.currency,
        lines=lines,
        total=sum(line.amount for line in lines),
        disclaimer=DISCLAIMER,
    )
