# Plan (bugfix): Foundational addresses from the postal address question
Status: done 2026-11-13. Requested by Daniel 2026-11-13 ("take information from that field and fill out the address rows... State should be 3 letters maximum and country should be in CAPITAL letters").

Departures from the plan as written:
- The reported empty phone was the Standard format, which has no phone column: Daniel had built his Foundational export with Standard selected (no class picked, title "test 4"). With his yes, an export whose rows carry a postal address now suggests the Foundational format. Surface addition: `backend/app/api/class_lists.py`.

## Why

Daniel ran his Foundational export through the Class Lists page (PR #19) and the address columns of the workbook came out empty. The address is typed into the form question "Enter your complete Postal Address, including country and postal code"; the page should split that into add1, add2, city, state, zip and country, with the state at most 3 letters and the country in capitals.

## Observed (2026-11-13)

- Today's export carries Corsizio's own columns before the form questions: `Phone`, `Address`, `Address: City`, `Address: State/Province`, `Address: Country`, `Address: Zip/Postal Code`. Of 9 rows, all 9 have a phone and an answer to the postal address question; Corsizio's five address columns are empty in every row. Counts only, checked outside the repository.
- `parse` takes the first column whose name contains "postal". That is now `Address: Zip/Postal Code`, so every address arrives empty. The September-to-October exports had no Corsizio address columns, which is why the end-to-end check passed then.
- With the right column, the current split fills all 3 first-timers' addresses (one of them flagged: the person gave no state, postcode or country). The 6 repeaters stay without an address, as in Daniel's 2026-10-16 list (3 first-timers with addresses, 6 repeaters without).
- The phone column came through for 9 of 9 in a build through the live API; no phone defect reproduced.
- `split_address` knows state abbreviations only; "Victoria" or "New South Wales" would be a miss. "Perth, Western Australia" would take "Australia" for the country and leave "Western" in the suburb.

## Acceptance criteria

1. An export with Corsizio's own address columns before the postal address question fills the address from the question.
2. A state typed in full (New South Wales, Victoria, Queensland, Western Australia, South Australia, Tasmania, Australian Capital Territory, Northern Territory) becomes its abbreviation; no split ever returns a state longer than 3 letters.
3. The country is always in capitals.

## Surface

- `backend/app/class_lists.py`: the address column; Australian state names
- `backend/tests/test_class_lists.py`: regression tests
- `docs/adr/0011-class-lists-built-not-stored.md`: the address rule line
- this plan, `docs/sessions/session_<stamp>.md`, `NEXT-STEPS.md`

## Design

- The address column is the one named "postal address" (the form question), then any "address" column that is not an email. One line.
- `AU_STATES` becomes a map from full name and abbreviation to the abbreviation; the state regex is built from its keys, longest first. "Australia" right after "Western" or "South" is the state, not the country.
- No new dependency, no frontend change.

## Test plan

- Unit, written first and seen red: a CSV in today's column order (invented values) parses the address from the question; `split_address` cases with full state names and a lower-case country; `test_split_address` also asserts every state is at most 3 letters and every country is in capitals.
- E2E: today's export through the Vite proxy, Foundational picked; count filled address cells per column. Counts only.

## Records

- Architecture map delta: none (no new flow or invariant).
- ADR: no new ADR; ADR-0011's address line names the full state names.

## Cross-repo impact

None.

## Open questions

- None.

## BACKLOG

- (none yet)
