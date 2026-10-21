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
- A student with no class tags is eligible for Foundational Training only.

## 2. What a student has completed

Read from their **full-word class tags** (ADR-0006): Foundational, Magical
Structures, Sensing I, Omega, MultiFrequency, Jewel and so on. Abbreviated or
dated tags (`SRA`, `CV+`, `MS-Cert`, `26-01-DM`) are ignored for now.

Completing a class implies the class it hangs off on the chart: a student
tagged LifeForm has done Multi-Frequency, Karmic Intensive, Magical Structures
and Foundational; a student tagged Sensing I has done Magical Structures.
"Also requires" boxes are not implied.

Checked 2026-10-21 against `APAC Wizards - Next Eligible Class.xlsx`: 120 of
128 students get the same next class. The 8 differences are 4 students with no
class tags, 3 whose completions are only in abbreviated tags (e.g. a `CKC` tag
for Clearing the Kundalini Channel), and 1 where the spreadsheet followed the
old, wrong prerequisites.

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
- If a reminder date has already passed when a class is added, skip that reminder. Don't send it late.
- Every send is reviewed and approved by a person before it goes out. Nothing sends automatically.
- For now, reminders and campaigns go to the APAC Wizards list only.

## 4. Student status labels

New Inquiry · Awaiting Prerequisite · Eligible · Enrolled · Confirmed ·
Attended · Completed · Repeat/Follow-up Needed · On Hold
