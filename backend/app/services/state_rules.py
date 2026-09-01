"""State-level ASU&H rules (roadmap S13, scaffold).

Ayurvedic (ASU&H) drug manufacturing and sales licences are issued by each
state's Licensing Authority under the Drugs and Cosmetics framework, and states
add their own procedural rules. Those state rules are not in the corpus.

This module ships:
  - a directory of state Licensing Authorities (the part that is stable and
    publicly known), served via /state-rules;
  - the ingestion hook (`STATE_RULES_DIR`) for per-state rule overlays that a
    later slice can populate — absent by default.
"""
from __future__ import annotations

import json
from pathlib import Path

from app.config import get_settings
from app.core.logging import get_logger
from app.schemas import StateAuthority, StateRulesResponse

logger = get_logger(__name__)

_AS_OF = "2024-01-01"

_NOTE = (
    "ASU&H drug licences are issued by the state Licensing Authority. State "
    "procedural rules are not in this corpus — confirm requirements and forms "
    "with the authority below. This directory is indicative and may be out of "
    "date."
)

_AUTHORITIES: list[StateAuthority] = [
    StateAuthority(
        key="kerala", state="Kerala",
        authority="Drugs Controller, Kerala (Ayurveda wing) — State Licensing "
        "Authority for ISM",
        portal_url="https://dc.kerala.gov.in/",
    ),
    StateAuthority(
        key="karnataka", state="Karnataka",
        authority="Drugs Control Department, Karnataka — Licensing Authority "
        "(Ayurveda/Unani)",
        portal_url="https://drugscontrol.karnataka.gov.in/",
    ),
    StateAuthority(
        key="maharashtra", state="Maharashtra",
        authority="Food and Drug Administration, Maharashtra — Ayurvedic, "
        "Siddha & Unani section",
        portal_url="https://fda.maharashtra.gov.in/",
    ),
    StateAuthority(
        key="tamil_nadu", state="Tamil Nadu",
        authority="Directorate of Indian Medicine and Homoeopathy / Drugs "
        "Control, Tamil Nadu",
        portal_url="https://www.tnhealth.tn.gov.in/",
    ),
    StateAuthority(
        key="uttar_pradesh", state="Uttar Pradesh",
        authority="Ayurvedic & Unani Services / Licensing Authority, U.P.",
        portal_url="https://ayush.up.gov.in/",
    ),
    StateAuthority(
        key="madhya_pradesh", state="Madhya Pradesh",
        authority="Food and Drug Administration, Madhya Pradesh — AYUSH licensing",
        portal_url="https://mpfda.gov.in/",
    ),
    StateAuthority(
        key="gujarat", state="Gujarat",
        authority="Food and Drugs Control Administration, Gujarat — Ayurvedic "
        "drug licensing",
        portal_url="https://fdca.gujarat.gov.in/",
    ),
    StateAuthority(
        key="rajasthan", state="Rajasthan",
        authority="Drugs Control Organisation, Rajasthan — Ayurved section",
        portal_url="https://dco.rajasthan.gov.in/",
    ),
    StateAuthority(
        key="delhi", state="Delhi (NCT)",
        authority="Drugs Control Department, GNCT of Delhi — ASU licensing",
        portal_url="https://dgehs.delhi.gov.in/",
    ),
    StateAuthority(
        key="west_bengal", state="West Bengal",
        authority="Directorate of Drugs Control, West Bengal — ASU wing",
        portal_url="https://wbhealth.gov.in/",
    ),
    StateAuthority(
        key="uttarakhand", state="Uttarakhand",
        authority="Ayurvedic & Unani Licensing Authority, Uttarakhand",
        portal_url="https://ayush.uk.gov.in/",
    ),
    StateAuthority(
        key="other", state="Other / not listed",
        authority="Contact the ASU&H Licensing Authority of the state where "
        "manufacture will take place.",
    ),
]

_BY_KEY = {a.key: a for a in _AUTHORITIES}


def _overlay_note(key: str) -> str | None:
    """Ingestion hook: extra state-rule notes from data/state_rules/<key>.json."""
    d = getattr(get_settings(), "state_rules_dir", "")
    if not d:
        return None
    p = Path(d) / f"{key}.json"
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data.get("note")
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("state rules overlay %s unreadable (%s)", p, exc)
        return None


def list_authorities() -> StateRulesResponse:
    authorities: list[StateAuthority] = []
    for a in _AUTHORITIES:
        extra = _overlay_note(a.key)
        authorities.append(a.model_copy(update={"note": extra}) if extra else a)
    return StateRulesResponse(as_of=_AS_OF, note=_NOTE, authorities=authorities)


def get_authority(key: str) -> StateAuthority | None:
    a = _BY_KEY.get(key)
    if a is None:
        return None
    extra = _overlay_note(key)
    return a.model_copy(update={"note": extra}) if extra else a
