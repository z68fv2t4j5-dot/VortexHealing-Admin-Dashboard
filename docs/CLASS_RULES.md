# Class Rules: Prerequisites and Reminder Timing

The source of truth for class eligibility and reminder emails. Paste this file
into any AI prompt that touches enrollment, eligibility or reminders. Do not
let a model guess these rules.

## 1. Prerequisites

**Authority:** the VortexHealing flowchart of trainings 2026-2028 (updated
2026-07-29), kept as `flowchart.pdf` in the VortexHealing Assistant Docs folder.
**In code:** `backend/app/class_rules.py`, transcribed from it. When the chart
changes, change that file, then this section.

How to read the chart:
- The **spine** is the bold boxes down the middle: Foundational Training →
  Magical Structures → Karmic Intensive → Multi-Frequency → LifeForm → OMEGA &
  the Karmic Body → Core Veil & Awakening to Being Awareness. After Core Veil
  it splits: Jewel (also needs Genetics & MF Devices), and Inner Veil → Being-IS
  & Universal Veil. Jewel + Being-IS → Merlin's Grace; Being-IS → I-Point &
  (no)Self; Merlin's Grace + I-Point → Original Veil/UAP → Awakening to
  Divinity (also needs Awakening the BodyMind) → Accessing Manifesting Intention
  and Deepening in Divinity, both → Magical Jewel.
- A **side class** becomes available at the level of the spine class it hangs
  off, plus any "also requires" box on the chart. Example: Sensing II needs
  OMEGA and Sensing I.

Decisions on boxes that are not plain prerequisites (approved 2026-10-21):
- Angelic Heart I: LifeForm, and Sensing I **or** Jewel.
- Awakening Bodymind II: Awakening to Divinity, and AMI **or** Deepening in Divinity.
- Transformation Days: eligible after Awakening to Divinity.
- Divine Magic II: never offered automatically; the repeat rule needs a person.
- TimeStreams, TimeStreams Lite, Divine Magic I: given inside other classes, never scheduled.
- Every student on the APAC Wizards list has completed Foundational Training (Daniel, 2026-10-21), whatever their tags say.

## 2. What a student has completed

Read from their **full-word class tags** (ADR-0006), plus Foundational Training for everyone on the APAC Wizards list: Foundational, Magical
Structures, Sensing I, Omega, MultiFrequency, Jewel and so on. Abbreviated or
dated tags (`SRA`, `CV+`, `MS-Cert`, `26-01-DM`) are ignored for now.

Completing a class implies the class it hangs off on the chart: a student
tagged LifeForm has done Multi-Frequency, Karmic Intensive, Magical Structures
and Foundational; a student tagged Sensing I has done Magical Structures.
"Also requires" boxes are not implied.

Checked 2026-10-21 against `APAC Wizards - Next Eligible Class.xlsx`: 116 of
128 students get the same next class. The 12 differences are all spreadsheet
gaps: 8 untagged APAC Wizards the spreadsheet sent back to Foundational, 3 whose
completions appear only in abbreviated tags (e.g. a `CKC` tag for Clearing the
Kundalini Channel; abbreviations are deliberately ignored), and 1 where it
followed the old, wrong prerequisites.

## 3. Reminder timing

Taken from `APAC Class Email Reminder Alerts.ics`:

| Reminder | When | Send time |
|---|---|---|
| First notice | 2 months before class start | 09:05 Australia/Sydney |
| Second notice | 1 month before class start | 09:05 Australia/Sydney |
| Final notice | 2 weeks before class start | 09:05 Australia/Sydney |

Rules:
- Send each reminder only to students who are **eligible** for that class (sections 1 and 2).
- Don't email a student who has already completed or is enrolled in that class.
- A reminder stays on the Email page's "Reminders due" list from its date for 7 days, then drops off. It is never sent late (ADR-0007).
- Every reminder is reviewed and approved by a person before it goes out. Nothing sends automatically. Each class and stage can be approved once.
- Dates are Sydney dates. Months are calendar months; a 31st falls back to the month's last day.
- For now, reminders and campaigns go to the APAC Wizards list only.
- The daily digest (section 5, ADR-0010) tells Daniel about an unapproved reminder on its date, 3 days later, and on its last day (7 days after), giving the Amsterdam time it closes: Sydney midnight, 14:00 to 16:00 by season.

## 4. Student status labels

New Inquiry · Awaiting Prerequisite · Eligible · Enrolled · Confirmed ·
Attended · Completed · Repeat/Follow-up Needed · On Hold

## 5. Admin task timing

From Daniel, 2026-11-04. Every class in the schedule gets these four tasks (all classes are his):

| Task | Due |
|---|---|
| Check enrolled students' prerequisites | 14 days before the class starts |
| Send joining details | 2 days before the class starts |
| Follow-up email to attendees | 3 days after the class ends (a one-day class ends on its start) |
| Commission form | 14 days after the class ends |
| Revenue and expenses (quarterly) | the last day of the month after each quarter: 31 Jan, 30 Apr, 31 Jul, 31 Oct |

Rules:
- Admin task dates, hand-added task dates and the digest's 09:00 are Amsterdam dates and times; reminder dates stay Sydney dates (section 3).
- Tasks exist only for classes starting on or after 4 November 2026 and for quarters ending after it (`SINCE` in `backend/app/admin_tasks.py`).
- The Tasks page and the digest list a task from 7 days before it is due until it is ticked done; an overdue task is in every digest. The quarterly task also gets a heads-up line exactly 7 days before.
- The digest goes once a day from 09:00 Amsterdam time (later the same day if the Mac was asleep), and not at all on a day with nothing due today and nothing overdue.
