"""Class prerequisites, transcribed from the VortexHealing flowchart of trainings
2026-2028 (updated 2026-07-29), which is the authority. See docs/CLASS_RULES.md.

Each class hangs off one parent box on the chart (`after`). Spine classes are the
bold boxes down the middle. Completing any class implies the class it hangs off,
because a student cannot have reached it otherwise; a spine class also implies
the spine classes joined into it (Merlin's Grace implies Jewel). Side "also
requires" boxes are not implied: older students may predate today's chart.
`also` lists the chart's "also requires" boxes; `any_of` is an either/or
requirement. `manual` classes are never auto-eligible: a person decides.
"""
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Optional


@dataclass(frozen=True)
class Rule:
    after: Optional[str]
    also: tuple = ()
    any_of: tuple = ()
    spine: bool = False
    manual: Optional[str] = None


FOUNDATIONAL = "Foundational Training"
MS = "Magical Structures"
KI = "Karmic Intensive"
MF = "Multi-Frequency"
LIFEFORM = "LifeForm"
OMEGA = "OMEGA & the Karmic Body"
CORE_VEIL = "Core Veil & Awakening to Being Awareness"
JEWEL = "Jewel"
INNER_VEIL = "Inner Veil"
BEING_IS = "Being-IS & Universal Veil"
MERLINS_GRACE = "Merlin's Grace"
I_POINT = "I-Point & (no)Self"
ORIGINAL_VEIL = "Original Veil/UAP"
ATD = "Awakening to Divinity"
AMI = "Accessing Manifesting Intention"
DEEP_DIVINITY = "Deepening in Divinity"
MAGICAL_JEWEL = "Magical Jewel"
GENETICS = "Genetics & MF Devices"
BODYMIND = "Awakening the BodyMind"

CLASSES = {
    # Spine
    FOUNDATIONAL: Rule(after=None, spine=True),
    MS: Rule(after=FOUNDATIONAL, spine=True),
    KI: Rule(after=MS, spine=True),
    MF: Rule(after=KI, spine=True),
    LIFEFORM: Rule(after=MF, spine=True),
    OMEGA: Rule(after=LIFEFORM, spine=True),
    CORE_VEIL: Rule(after=OMEGA, spine=True),
    JEWEL: Rule(after=CORE_VEIL, also=(GENETICS,), spine=True),
    INNER_VEIL: Rule(after=CORE_VEIL, spine=True),
    BEING_IS: Rule(after=INNER_VEIL, spine=True),
    MERLINS_GRACE: Rule(after=BEING_IS, also=(JEWEL,), spine=True),
    I_POINT: Rule(after=BEING_IS, spine=True),
    ORIGINAL_VEIL: Rule(after=MERLINS_GRACE, also=(I_POINT,), spine=True),
    ATD: Rule(after=ORIGINAL_VEIL, also=(BODYMIND,), spine=True),
    AMI: Rule(after=ATD, spine=True),
    DEEP_DIVINITY: Rule(after=ATD, spine=True),
    MAGICAL_JEWEL: Rule(after=AMI, also=(DEEP_DIVINITY,), spine=True),

    # Off Foundational Training
    "Deepening with Merlin": Rule(after=FOUNDATIONAL),
    "Creating a Professional Practice I": Rule(after=FOUNDATIONAL),
    "Creating a Professional Practice II": Rule(after=FOUNDATIONAL, also=("Creating a Professional Practice I",)),
    "Unwinding the Fascia Energy": Rule(after=FOUNDATIONAL),
    "Clearing the Kundalini Channel": Rule(after=FOUNDATIONAL),
    "Bringing Consciousness to Form": Rule(after=FOUNDATIONAL),
    "Earthshifts": Rule(after=FOUNDATIONAL),
    # Off Magical Structures
    "Sensing I": Rule(after=MS),
    # Off Multi-Frequency
    "Breaking TimeLines": Rule(after=MF),
    GENETICS: Rule(after=MF),
    # Off LifeForm
    "InterDimensional Vortex": Rule(after=LIFEFORM),
    "Angelic Heart I": Rule(after=LIFEFORM, any_of=("Sensing I", JEWEL)),
    "Angelic Connection": Rule(after="Angelic Heart I"),
    # Off OMEGA
    "EarthWorks I": Rule(after=OMEGA),
    "Sensing II": Rule(after=OMEGA, also=("Sensing I",)),
    "Presence": Rule(after=OMEGA),
    # Off Core Veil
    "EarthWorks II": Rule(after=CORE_VEIL, also=("EarthWorks I",)),
    "EarthWorks III": Rule(after="EarthWorks II", also=(MERLINS_GRACE, I_POINT)),
    "Bringing Consciousness Thru Form": Rule(after=CORE_VEIL, also=("Bringing Consciousness to Form",)),
    "Angelic Heart II & III": Rule(after=CORE_VEIL),
    "Merlin's Puzzle": Rule(after=CORE_VEIL, also=("Sensing I",)),
    "Opening the Creative Channel": Rule(after=CORE_VEIL),
    "Connecting with Quinstel": Rule(after=CORE_VEIL),
    "Deepening Awakeness & Embodiment": Rule(after=CORE_VEIL),
    "Sensing III": Rule(after=CORE_VEIL, also=("Sensing II",)),
    # Off Jewel, Merlin's Grace, I-Point
    "Quantum Gate": Rule(after=JEWEL),
    BODYMIND: Rule(after=MERLINS_GRACE),
    "Breaking with the Past I": Rule(after=I_POINT, also=(JEWEL,)),
    # Off Original Veil
    "DNA: Transforming DNA's Core Program": Rule(after=ORIGINAL_VEIL, also=(BODYMIND,)),
    "Angelic Heart IV": Rule(after=ORIGINAL_VEIL, also=("Angelic Heart II & III",)),
    "Angelic Heart V": Rule(after="Angelic Heart IV"),
    "Sensing IV": Rule(after=ORIGINAL_VEIL, also=("Sensing III",)),
    # Off Awakening to Divinity and below
    "Transformation Days": Rule(after=ATD),
    "Sensing V": Rule(after=ATD, also=("Sensing IV",)),
    "Breaking with the Past II": Rule(after=ATD, also=("Breaking with the Past I",)),
    "Awakening Bodymind II": Rule(after=ATD, any_of=(AMI, DEEP_DIVINITY)),
    "EarthWorks IV": Rule(after=AMI, also=("EarthWorks III",)),
    "EarthWorks V": Rule(after="EarthWorks IV"),
    "Kundalini II": Rule(after=DEEP_DIVINITY, also=("Clearing the Kundalini Channel",)),
    "Divine Magic II": Rule(after=MAGICAL_JEWEL, manual="needs a repeat of Magical Jewel, ATD or MI after Magical Jewel"),
}

# Other spellings in student tags and the class schedule, lowercased
ALIASES = {
    "foundational": FOUNDATIONAL,
    "multifrequency": MF,
    "multi-frequency & merlin's jewel": MF,
    "omega": OMEGA,
    "omega & the karmic body": OMEGA,
    "genetics": GENETICS,
    "timelines": "Breaking TimeLines",
    "clearing kundalini": "Clearing the Kundalini Channel",
    "deepening in meditation": "Deepening with Merlin",
    "deepening in meditation with merlin": "Deepening with Merlin",
    "sensing i: psychic and consciousness development": "Sensing I",
    "merlin's grace & multi-dimensional healing": MERLINS_GRACE,
    "earthworks": "EarthWorks I",
}

_LOOKUP = {name.lower(): name for name in CLASSES} | ALIASES
_TRAILING_NOTE = re.compile(r"\s*\([^)]*\)$")


def class_for(name: str) -> Optional[str]:
    """Flowchart class for a tag or schedule name; None for anything else (e.g. 'SRA', '26-01-DM')."""
    key = _TRAILING_NOTE.sub("", (name or "").replace("’", "'").strip()).lower()
    return _LOOKUP.get(key)


def completed_from_tags(tags: str) -> set:
    """Classes a student has completed, from their comma-separated tags."""
    done = {c for c in (class_for(t) for t in (tags or "").split(",")) if c}
    stack = list(done)
    while stack:
        rule = CLASSES[stack.pop()]
        implied = (rule.after, *rule.also) if rule.spine else (rule.after,)
        for parent in implied:
            if parent and (parent == rule.after or CLASSES[parent].spine) and parent not in done:
                done.add(parent)
                stack.append(parent)
    return done


def is_eligible(cls: str, completed: set) -> bool:
    rule = CLASSES[cls]
    if rule.manual:
        return False
    required = ([rule.after] if rule.after else []) + list(rule.also)
    return all(r in completed for r in required) and (not rule.any_of or any(r in completed for r in rule.any_of))


def next_class(completed: set, schedule: Iterable, today: datetime) -> Optional[str]:
    """Name of the earliest scheduled class from `today` that the student has not taken and is eligible for.

    `schedule` is (schedule name, start datetime) pairs; names not on the flowchart are skipped."""
    for name, start in sorted(schedule, key=lambda s: s[1]):
        cls = class_for(name)
        if start >= today and cls and cls not in completed and is_eligible(cls, completed):
            return name
    return None
