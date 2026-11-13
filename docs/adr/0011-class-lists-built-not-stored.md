# ADR-0011: Class lists are built from an upload in memory and never stored; Daniel's ticks decide the repeaters

**Status:** Accepted. **Date:** 2026-11-12. **Trigger:** Daniel asked for his class list workbooks to be made on the dashboard instead of in a claude.ai chat or a local script.

## Context

Before each class Daniel downloads a Corsizio attendee export (a CSV with a generic file name) and turns it into a class list workbook. Since September 2026 that was done in a claude.ai chat, then by a local script outside this repository; he moved several people to Repeaters by hand every time. The exports hold names, emails and, for Foundational, phone numbers and postal addresses. Daniel decided on 2026-11-12: upload, review, then download; addresses split by rules, with misses flagged rather than looked up; repeaters suggested from his records as well; Foundational rows numbered.

## Decision

- **Nothing is stored.** The page reads the CSV in the browser and sends its text; `POST /api/class-lists/preview` returns the suggestions and `POST /api/class-lists/build` returns the workbook. Neither writes to the database or the disk. The export stays in Daniel's Downloads and the workbook is the record.
- **Repeaters**, in order: a coupon code makes a repeater (Daniel's rule of 2026-09-16; codes other than VHREPEATER are marked for checking); then the Foundational form's "first time or repeater" answer; then a suggestion when the student's class tags (ADR-0006) already include the class. Every suggestion shows its reason, and Daniel's ticks are final.
- **Two formats.** Every class but Foundational: the layout of the September and October lists (merged title, numbered rows by surname, a Repeaters section with numbering carried on). Foundational: the layout of the 2026-10-16 list (title in F2, Verdana, phone and split address for first-timers, repeaters after them in yellow without an address), numbered. Foundational is chosen when the class picked or the title names it; the page can switch.
- **Titles** use the flowchart's short class name ("Sensing I", "Foundational"), the class date and "Daniel", as Daniel writes them.

## Consequences

- No class list data accumulates on the Mac beyond what Daniel downloads; a list cannot be reopened on the dashboard later, only rebuilt from the export.
- Tag suggestions can be wrong: a student tagged after attending the class being listed shows as "done" (5 such suggestions across the four October lists, against 19 of Daniel's 26 hand-picked repeaters found). Daniel unticks them.
- The address comes from the form's postal address question. The rules know Australian states, typed in full or short and always written short (3 letters at most), and four-digit postcodes; the country is written in capitals (Daniel, 2026-11-13). Overseas and incomplete addresses are flagged, never guessed, so Daniel still finishes some by hand.
- `openpyxl` joins both requirements files.

## Alternatives rejected

- Keeping uploads for an audit trail: more personal data at rest for no use Daniel named.
- Splitting addresses with local Qwen: better on messy addresses, but slow, needs LM Studio running and can invent a part; Daniel chose rules with flags.
- A multipart file upload: needs `python-multipart` in CI for one field; the CSV is small enough to send as JSON text.
