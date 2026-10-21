# Plan (feature): class rules from the flowchart, APAC-only email scope
Status: done 2026-10-21. Departures: completing a side class implies the class it hangs off (found while checking against the spreadsheet; the plan said spine only). 120 of 128 match; the 8 differences are listed in docs/CLASS_RULES.md section 2.

## Investigation

Observed:
- `flowchart.pdf` (VortexHealing flowchart of trainings 2026-2028, updated 2026-07-29) is the authority for prerequisites (Daniel, 2026-10-21). Bold classes form a spine; a side class requires the spine class it hangs off plus any "also requires" class in its box.
- The `classes.prerequisites` column seeded by `seed_classes.py` disagrees with the flowchart on most rows (e.g. Sensing I seeded as "None", flowchart puts it after Magical Structures).
- 128 students are on the APAC Wizards list. Their tags mix full class names (Foundational, Magical Structures, Sensing I, Omega, Jewel...) with abbreviated or dated ones (SRA, CV+, MS-Cert, 26-01-DM).
- `APAC Wizards - Next Eligible Class.xlsx` lists, for each of the 128, one next class. Spot checks match "the earliest scheduled class the student is eligible for and has not taken", reading the full-word tags as completed classes, and treating a spine class as implying every spine class above it.

Assumed (to confirm):
- Full-word class tags are the record of completed classes.
- Schedule names map onto flowchart classes: "Multi-Frequency & Merlin's Jewel" is Multi-Frequency; "Deepening in Meditation with Merlin" is Deepening with Merlin; "Sensing I: Psychic and Consciousness Development" is Sensing I; both "Connecting with Quinstel" timezones are Connecting w/Quinstel.

## Acceptance criteria

1. The Email composer offers only the APAC Wizards list, and its tag dropdown offers only full-word class tags present on APAC Wizards students.
2. A rules module answers "is this student eligible for class X" and "what is this student's next scheduled class", from the flowchart and the student's tags.
3. Run locally against the real data, the next-class answer matches the spreadsheet for all 128 APAC Wizards students, or every mismatch is listed with its reason.
4. `docs/CLASS_RULES.md` no longer carries ⚠ rows; prerequisites point at the module.

Surface: backend/app/class_rules.py (new), backend/app/api/email_campaigns.py, backend/tests/test_class_rules.py (new), backend/tests/test_email_campaigns.py, frontend/src/pages/Email.tsx, docs/CLASS_RULES.md, docs/ARCHITECTURE.md, docs/adr/0006-class-tags-are-completions.md (new), docs/adr/README.md, AGENTS.md (bmad:context lines on class rules), .continue/rules/project.md, NEXT-STEPS.md, docs/sessions/session_<stamp>.md, this plan.

## Design

- `class_rules.py`: one dict transcribed from the flowchart (class -> spine parent, extra requirements, "any of" requirements, tag aliases) plus three functions: `completed_from_tags`, `is_eligible`, `next_class`. Plain Python data: the rules change a few times a year, and a dict reviewed against the PDF is easier to check than a database table.
- `GET /api/email/options` returns `{lists: ["APAC Wizards"], tags: [full-word class tags found on those students]}`. Email.tsx calls it instead of downloading every student to build dropdowns. The APAC-only scope is one constant in the backend, so widening it later is a one-line change.
- Verification script: not committed (it reads real student data). Run once, and its summary (match count, anonymised mismatches) goes in the session log.
- No database change. Fixing `seed_classes.py` prerequisites is BACKLOG.

## Test plan

Unit: spine implication (LifeForm implies Magical Structures); side class needs its spine parent; "also requires" (Sensing II needs OMEGA and Sensing I); "any of" (Angelic Heart I needs LifeForm and Sensing I or Jewel); join (Merlin's Grace needs Jewel and Being-IS); tag aliasing (Omega, MultiFrequency, Clearing Kundalini, Deepening In Meditation); abbreviated tags ignored; `next_class` skips taken and ineligible classes and picks the earliest date; `/api/email/options` returns only APAC Wizards and full-word tags. All with synthetic students.
E2E: n/a, the frontend has no test runner; manual check of the Email page in the browser.

Architecture map delta: yes (new module, eligibility flow). ADR: yes, 0006 (tags as the completion record).
Cross-repo impact: none.

## Rules that need a decision (flowchart conditions that are not plain prerequisites)

Recommended handling in brackets:
- Angelic Heart I: "also requires Sensing I or Jewel" [any-of rule].
- Divine Magic II: needs a repeat of Magical Jewel, ATD or MI after Magical Jewel [never auto-eligible; manual].
- Transformation Days: "sometimes requires MI" [eligible after Awakening to Divinity; note says check the event].
- Awakening Bodymind II: needs MI or Deepening in Divinity; 10-day version needs MJ; given from 2028 [any-of MI / Deepening in Divinity].
- TimeStreams, TimeStreams Lite, Divine Magic I: given inside other classes [not schedulable; excluded].
- Earthshifts: free virtual event [eligible after Foundational, like the chart shows].

## Open questions

- Are full-word tags the completion record? [Recommended: yes; confirmed if the spreadsheet comparison matches.]
- Should students with no class tags at all be eligible for Foundational Training? [Recommended: yes; it has no prerequisite.]

## BACKLOG

- `seed_classes.py` prerequisites column is wrong for most classes; regenerate it from `class_rules.py`.
- `backend/app/api/emails.py` (old router) uses fields the model no longer has.
