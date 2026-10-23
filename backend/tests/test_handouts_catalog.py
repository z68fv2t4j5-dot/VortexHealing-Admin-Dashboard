from handouts.catalog import KEEP, NEEDS_DECISION, RETIRED, SKIPPED, build_catalog, family_and_version


def decisions(paths, overrides=None):
    return {e.path: e for e in build_catalog(paths, overrides)}


def test_old_folders_redlines_and_non_text_files_are_skipped():
    got = decisions([
        "Tools/OLD/Tool-Review-3.doc",
        "Tools/old/Tool-Review-2.pdf",
        "Tool-Review-4-Redline.doc",
        "Tool-Review-4.m4a",
        "Extras.zip",
        "~$Tool-Review-4.doc",
        "Tool-Review-4.doc",
    ])
    assert got["Tool-Review-4.doc"].decision == KEEP
    for path in ("Tools/OLD/Tool-Review-3.doc", "Tools/old/Tool-Review-2.pdf", "Tool-Review-4-Redline.doc",
                 "Tool-Review-4.m4a", "Extras.zip", "~$Tool-Review-4.doc"):
        assert got[path].decision == SKIPPED, path


def test_highest_version_wins_and_edit_does_not_outrank_a_higher_number():
    got = decisions(["XY-Review-19.doc", "XY-Review-19-Edit.doc", "XY-Review-20-Edit.doc"])
    assert got["XY-Review-20-Edit.doc"].decision == KEEP
    for path in ("XY-Review-19.doc", "XY-Review-19-Edit.doc"):
        assert got[path].decision == RETIRED
        assert got[path].superseded_by == "XY-Review-20-Edit.doc"


def test_doc_is_kept_over_a_pdf_of_the_same_version():
    got = decisions(["Topic-Notes-7.pdf", "Topic-Notes-7.doc", "Topic-Notes-6.pdf"])
    assert got["Topic-Notes-7.doc"].decision == KEEP
    assert got["Topic-Notes-7.pdf"].decision == SKIPPED
    assert got["Topic-Notes-6.pdf"].decision == RETIRED


def test_letter_and_for_pdf_copies_lose_to_the_plain_file():
    got = decisions(["Land-Review-6.doc", "Land-Review-6-letter.doc", "Form-5-for-PDF.doc"])
    assert got["Land-Review-6.doc"].decision == KEEP
    assert got["Land-Review-6-letter.doc"].decision == SKIPPED
    assert got["Form-5-for-PDF.doc"].decision == KEEP


def test_letter_revisions_order_after_their_number():
    paths = ["Land5-Review-1J.doc", "Land5-Review-1K.doc", "Land5-Review-2.doc", "Land5-Review-2-A.doc"]
    assert family_and_version("Land5-Review-2-A.doc") == ("land5-review", (2, "a"), False)
    got = decisions(paths)
    assert got["Land5-Review-2-A.doc"].decision == KEEP
    assert {got[p].decision for p in paths[:3]} == {RETIRED}


def test_condensed_and_complete_are_separate_handouts():
    got = decisions(["Base-History4-condensed.doc", "Base-History6-Complete.doc"])
    assert got["Base-History4-condensed.doc"].decision == KEEP
    assert got["Base-History6-Complete.doc"].decision == KEEP


def test_same_handout_in_two_folders_is_kept_once():
    got = decisions(["A/Shared-Info-1.doc", "B/Shared-Info-1.doc"])
    assert sorted(e.decision for e in got.values()) == [KEEP, SKIPPED]


def test_dated_names_wait_for_a_decision_unless_overridden():
    paths = ["Guide-2021-Mar-3.pdf", "Guide-2021-Sep.pdf"]
    assert {e.decision for e in build_catalog(paths)} == {NEEDS_DECISION}
    got = decisions(paths, {"Guide-2021-Sep.pdf": "KEEP", "Guide-2021-Mar-3.pdf": "RETIRE"})
    assert got["Guide-2021-Sep.pdf"].decision == KEEP
    assert got["Guide-2021-Mar-3.pdf"].decision == RETIRED


def test_overrides_win_over_the_version_rule():
    got = decisions(["Item-2.doc", "Item-3.doc"], {"Item-3.doc": "SKIP"})
    assert got["Item-3.doc"].decision == SKIPPED
    assert got["Item-2.doc"].decision == KEEP


def test_default_overrides_keep_the_2026_foundational_manual_only():
    got = decisions([
        "F/2026-Foundational-Manual-(Oct 1)-Letter.pdf",
        "F/Foundational-Manual-2022-Feb-26.pdf",
        "F/Foundational-Training-Manual-2022-Nov.pdf",
    ])
    assert got["F/2026-Foundational-Manual-(Oct 1)-Letter.pdf"].decision == KEEP
    assert got["F/Foundational-Manual-2022-Feb-26.pdf"].decision == RETIRED
    assert got["F/Foundational-Training-Manual-2022-Nov.pdf"].decision == RETIRED
