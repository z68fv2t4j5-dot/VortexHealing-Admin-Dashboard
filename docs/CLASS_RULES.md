# Class Rules: Prerequisites and Reminder Timing

The source of truth for class eligibility and reminder emails. Paste this file
into any AI prompt that touches enrollment, eligibility or reminders. Do not
let a model guess these rules.

> **Status: DRAFT. Daniel to verify.** The prerequisite table below was
> copied from the `classes.prerequisites` column in `backend/vortexhealing.db`
> (seeded by `seed_classes.py`) and from `Class Admin Workflow Draft.md`. Rows
> marked ⚠ look questionable. Correct them here first, then update
> `seed_classes.py` to match.

## 1. Reminder timing

Taken from `APAC Class Email Reminder Alerts.ics`:

| Reminder | When | Send time |
|---|---|---|
| First notice | 2 months before class start | 09:05 Australia/Sydney |
| Second notice | 1 month before class start | 09:05 Australia/Sydney |
| Final notice | 2 weeks before class start | 09:05 Australia/Sydney |

Rules:
- Send each reminder only to students who are **eligible** for that class (see §2).
- Don't email a student who is already enrolled in that class.
- If a reminder date has already passed when a class is added, skip that reminder. Don't send it late.
- Every send is reviewed and approved by a person before it goes out. Nothing sends automatically.

## 2. Prerequisites

A student is eligible for a class when they have completed **every** class
listed in its "Requires" column.

| Class | Requires | Notes |
|---|---|---|
| Sensing I: Psychic and Consciousness Development | none | Entry class |
| Sensing II | Sensing I | Confirmed in workflow draft |
| Sensing III | Sensing II | Confirmed in workflow draft |
| Clearing the Kundalini Channel | Sensing I | |
| Magical Structures | Sensing I | ⚠ verify; workflow draft orders it after Foundational Training |
| Foundational Training | Sensing I | ⚠ verify; may be an entry class |
| Connecting with Quinstel (all timezones) | Sensing II | |
| Deepening in Meditation with Merlin | "Basic meditation" | ⚠ not a class name; replace with a real class or "none" |
| Karmic Intensive | Sensing II | ⚠ verify; workflow draft orders it after Magical Structures |
| Multi-Frequency & Merlin's Jewel | Sensing III | |
| InterDimensional Vortex | Sensing II | |
| LifeForm | Sensing II | |
| OMEGA & The Karmic Body | Sensing III | |
| Merlin's Grace & Multi-Dimensional Healing | Sensing III | |
| EarthWorks I | Sensing I | |
| EarthWorks II | EarthWorks I | From workflow draft |
| EarthWorks IV | EarthWorks III | From workflow draft |
| Presence | Sensing II | |

Special cases (from `Class Admin Workflow Draft.md`):
- Jewel is required before certain advanced trainings. ⚠ List which ones.
- Magical Jewel / MI / MJ repeaters may receive Divine Magic I.
- Any exception must be approved by the teacher and recorded in the student's notes.

## 3. Where completion history comes from

⚠ To decide. Right now the database has no table of which student completed
which class. The candidates are:
- the class list spreadsheets in `VortexHealing Assistant Docs/`
  (e.g. `Sensing I Class List October 3 2026 Daniel.csv`)
- the `tags` field on students (e.g. `CV+`, `Foundational`, `SRA`)
- `APAC Wizards - Next Eligible Class.xlsx` (already lists each student's next eligible class)

Pick one source. The eligibility check can't be automated until it exists.

## 4. Student status labels

New Inquiry · Awaiting Prerequisite · Eligible · Enrolled · Confirmed ·
Attended · Completed · Repeat/Follow-up Needed · On Hold
