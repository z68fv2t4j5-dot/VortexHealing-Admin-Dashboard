from datetime import datetime

from app.class_rules import CLASSES, class_for, completed_from_tags, is_eligible, next_class


def test_every_requirement_names_a_class_on_the_chart():
    for rule in CLASSES.values():
        for req in ([rule.after] if rule.after else []) + list(rule.also) + list(rule.any_of):
            assert req in CLASSES


def test_tag_and_schedule_spellings_map_to_chart_classes():
    assert class_for("Omega") == "OMEGA & the Karmic Body"
    assert class_for("MultiFrequency") == "Multi-Frequency"
    assert class_for("Multi-Frequency & Merlin’s Jewel") == "Multi-Frequency"
    assert class_for("Clearing Kundalini") == "Clearing the Kundalini Channel"
    assert class_for("Deepening In Meditation") == "Deepening with Merlin"
    assert class_for("Sensing I: Psychic and Consciousness Development (September)") == "Sensing I"
    assert class_for("Connecting with Quinstel (Asia and Europe Timezone)") == "Connecting with Quinstel"


def test_abbreviated_and_dated_tags_are_not_classes():
    for tag in ("SRA", "CV+", "MS-Cert", "26-01-DM", "25-12-KI", ""):
        assert class_for(tag) is None


def test_a_spine_class_implies_the_spine_above_it():
    done = completed_from_tags("LifeForm, SRA")
    assert {"Foundational Training", "Magical Structures", "Karmic Intensive", "Multi-Frequency", "LifeForm"} <= done


def test_a_side_class_implies_the_spine_class_it_hangs_off():
    assert {"Sensing I", "Magical Structures", "Foundational Training"} == completed_from_tags("Sensing I")


def test_a_side_class_does_not_imply_its_also_requires():
    assert "Sensing I" not in completed_from_tags("Sensing II")


def test_a_spine_join_implies_both_branches():
    done = completed_from_tags("Merlin's Grace")
    assert {"Jewel", "Being-IS & Universal Veil", "Inner Veil", "Core Veil & Awakening to Being Awareness"} <= done
    assert "Genetics & MF Devices" not in done


def test_side_class_needs_its_spine_class():
    assert not is_eligible("Clearing the Kundalini Channel", set())
    assert is_eligible("Clearing the Kundalini Channel", completed_from_tags("Foundational"))


def test_also_requires_is_enforced():
    omega_only = completed_from_tags("Omega")
    assert not is_eligible("Sensing II", omega_only)
    assert is_eligible("Sensing II", omega_only | {"Sensing I"})


def test_any_of_needs_one_of_the_options():
    lifeform = completed_from_tags("LifeForm")
    assert not is_eligible("Angelic Heart I", lifeform)
    assert is_eligible("Angelic Heart I", lifeform | {"Sensing I"})


def test_spine_join_needs_both_branches():
    being_is = completed_from_tags("Being-IS & Universal Veil")
    assert not is_eligible("Merlin's Grace", being_is)
    assert is_eligible("Merlin's Grace", being_is | {"Jewel"})


def test_manual_classes_are_never_auto_eligible():
    assert not is_eligible("Divine Magic II", completed_from_tags("Magical Jewel"))


def test_foundational_needs_nothing():
    assert is_eligible("Foundational Training", set())


SCHEDULE = [
    ("Magical Structures", datetime(2026, 11, 11)),
    ("Clearing the Kundalini Channel", datetime(2026, 10, 31)),
    ("Sensing II", datetime(2026, 10, 4)),
    ("Foundational Training (May)", datetime(2027, 5, 12)),
    ("A workshop not on the chart", datetime(2026, 10, 20)),
]


def test_next_class_is_the_earliest_eligible_untaken_class_from_today():
    today = datetime(2026, 10, 6)
    assert next_class(completed_from_tags("Foundational"), SCHEDULE, today) == "Clearing the Kundalini Channel"
    assert next_class(completed_from_tags("Foundational, Clearing Kundalini"), SCHEDULE, today) == "Magical Structures"
    assert next_class(set(), SCHEDULE, today) == "Foundational Training (May)"


def test_next_class_is_none_when_nothing_fits():
    assert next_class(completed_from_tags("Magical Structures, Clearing Kundalini"), SCHEDULE, datetime(2026, 10, 6)) is None


def test_apac_wizards_have_completed_foundational():
    done = completed_from_tags("", "Free Events, APAC Wizards")
    assert done == {"Foundational Training"}
    assert is_eligible("Clearing the Kundalini Channel", done)


def test_other_lists_imply_nothing():
    assert completed_from_tags("", "Global Wizards, Free Events") == set()
