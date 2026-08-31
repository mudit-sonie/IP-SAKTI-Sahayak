"""Compliance checklist generator.

Rule-driven, deliberately not an LLM: each item is a known regulatory obligation
keyed on the formulation category, jurisdiction, and ABS status. Where the corpus
supports it, a targeted retrieval attaches a real citation to the item; when
retrieval is weak the item still ships, just without a citation (honest — the
obligation is real even if our corpus doesn't cover the exact provision yet).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.core.logging import get_logger
from app.retrieval import get_retriever
from app.schemas import ChecklistItem, ChecklistStatus, Citation, Matter
from app.store.repos import new_id

logger = get_logger(__name__)

_CITE_MIN_SCORE = 0.42


@dataclass
class Rule:
    key: str
    title: str
    group: str
    detail: str
    probe: str | None = None  # retrieval query to ground the item
    jurisdictions: tuple[str, ...] = ("india", "international")
    categories: tuple[str, ...] = ()  # empty = all
    abs_only: bool = False


_RULES: list[Rule] = [
    # --- India / therapeutic drugs -------------------------------------------
    Rule(
        "asu_manufacturing_licence",
        "Obtain a manufacturing licence for an Ayurvedic (ASU) drug",
        "Licensing",
        "Manufacture for sale of an Ayurvedic drug requires a licence from the "
        "State Licensing Authority under the Drugs and Cosmetics framework.",
        probe="licence to manufacture ayurvedic drug for sale",
        jurisdictions=("india",),
        categories=("classical", "proprietary", "new_drug", "phytopharmaceutical"),
    ),
    Rule(
        "gmp_schedule_t",
        "Meet Good Manufacturing Practice requirements (Schedule T)",
        "Licensing",
        "ASU drug manufacture must comply with the GMP requirements prescribed "
        "for Ayurvedic, Siddha and Unani medicines.",
        probe="good manufacturing practice ayurvedic siddha unani schedule",
        jurisdictions=("india",),
        categories=("classical", "proprietary", "new_drug", "phytopharmaceutical"),
    ),
    Rule(
        "label_particulars",
        "Ensure label particulars meet the Drugs and Cosmetics Rules",
        "Labelling",
        "Container and package labels must carry the prescribed particulars "
        "(true list of ingredients, licence number, manufacturer, etc.).",
        probe="label of ayurvedic medicine particulars ingredients licence number",
        jurisdictions=("india",),
        categories=("classical", "proprietary", "new_drug", "phytopharmaceutical", "cosmetic"),
    ),
    Rule(
        "no_prohibited_ad_claims",
        "Do not advertise prohibited disease claims",
        "Advertising",
        "The Drugs and Magic Remedies (Objectionable Advertisements) Act bars "
        "advertising a remedy for the diseases/conditions in its Schedule.",
        probe="advertisement magic remedies prohibited diseases schedule",
        jurisdictions=("india",),
        categories=("classical", "proprietary", "new_drug", "phytopharmaceutical"),
    ),
    Rule(
        "new_drug_approval",
        "Complete new-drug / safety and effectiveness requirements",
        "Approvals",
        "A formulation with a new chemical entity or new claims may require "
        "proof of safety and effectiveness before manufacture.",
        probe="proof of safety and effectiveness ayurvedic new drug",
        jurisdictions=("india",),
        categories=("new_drug", "phytopharmaceutical"),
    ),
    # --- IP ----------------------------------------------------------------
    Rule(
        "s3p_assessment",
        "Assess patentability under the traditional-knowledge bar",
        "IP",
        "Section 3(p) excludes inventions that are, in effect, traditional "
        "knowledge or an aggregation of known traditional properties.",
        probe="traditional knowledge not an invention section 3(p) patents",
        jurisdictions=("india",),
        categories=("classical", "proprietary"),
    ),
    Rule(
        "gi_conflict_check",
        "Check for a registered Geographical Indication on the product name",
        "IP",
        "A registered GI restricts use of the indication by non-authorised "
        "users; confirm your product name/claims do not infringe one.",
        probe="geographical indication registration prohibition of use goods",
        jurisdictions=("india",),
    ),
    # --- ABS (only when the matter is ABS-flagged) ------------------------
    Rule(
        "abs_prior_approval",
        "Obtain prior approval / intimation from the NBA or State Biodiversity Board",
        "ABS",
        "Commercial utilisation or IP based on a biological resource occurring "
        "in India needs prior approval of / intimation to the biodiversity "
        "authorities.",
        probe="previous approval national biodiversity authority commercial utilisation biological resource",
        jurisdictions=("india",),
        abs_only=True,
    ),
    Rule(
        "abs_disclosure_of_source",
        "Disclose the source and geographical origin of biological material in patent filings",
        "ABS",
        "Patent applications must disclose the source and geographical origin "
        "of any biological material used in the invention.",
        probe="disclosure source geographical origin biological material patent application",
        jurisdictions=("india",),
        abs_only=True,
    ),
    # --- International ----------------------------------------------------
    Rule(
        "trips_target_markets",
        "Confirm patent protection is available in each target market (TRIPS)",
        "IP",
        "TRIPS sets minimum standards but patentability and exclusions vary by "
        "member; check each target jurisdiction.",
        probe="patentable subject matter exclusions TRIPS article 27",
        jurisdictions=("international",),
    ),
    Rule(
        "nagoya_benefit_sharing",
        "Address CBD / Nagoya access and benefit-sharing for the source country",
        "ABS",
        "Access to genetic resources and associated traditional knowledge is "
        "subject to the provider country's ABS rules and mutually agreed terms.",
        probe="access genetic resources prior informed consent mutually agreed terms benefit sharing",
        jurisdictions=("international",),
    ),
]


def _ground(probe: str | None, jurisdiction: str) -> list[Citation]:
    if not probe:
        return []
    try:
        chunks, top = get_retriever().retrieve(
            probe, jurisdiction=jurisdiction, top_k=1
        )
    except Exception as exc:  # pragma: no cover - retrieval degraded
        logger.warning("checklist grounding failed for %r (%s)", probe, exc)
        return []
    if not chunks or top < _CITE_MIN_SCORE:
        return []
    c = chunks[0].chunk
    return [
        Citation(
            source=c.source,
            section=c.section,
            excerpt_ref=c.chunk_id,
            source_url=c.metadata.get("source_url"),
        )
    ]


def generate(matter: Matter) -> list[ChecklistItem]:
    jurisdiction = matter.jurisdiction.value
    category = (matter.formulation_category or "").lower()
    abs_flagged = matter.abs_status.value == "flagged"

    # preserve the status a user has already set, keyed on the rule
    prior = {i.source_rule: i for i in matter.checklist if i.source_rule}

    items: list[ChecklistItem] = []
    for rule in _RULES:
        if jurisdiction not in rule.jurisdictions:
            continue
        if rule.categories and category and category not in rule.categories:
            continue
        if rule.categories and not category:
            continue  # rule needs a classification we don't have
        if rule.abs_only and not abs_flagged:
            continue

        kept = prior.get(rule.key)
        items.append(
            ChecklistItem(
                id=kept.id if kept else new_id("c_"),
                title=rule.title,
                detail=rule.detail,
                group=rule.group,
                status=kept.status if kept else ChecklistStatus.todo,
                citations=_ground(rule.probe, jurisdiction),
                source_rule=rule.key,
            )
        )

    # keep any manually-added items (no source_rule) untouched
    items.extend(i for i in matter.checklist if not i.source_rule)
    return items
