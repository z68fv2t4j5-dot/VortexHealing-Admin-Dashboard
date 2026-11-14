# Plan (feature): class lists
Status: done 2026-11-12. Approved by Daniel 2026-11-12 ("yes numbered pls and goahead").

Departures from the plan as written:
- Foundational rows are numbered (`#` in column A), Daniel's answer to the open question; the table's medium edge moves to column A.
- Titles from the schedule use the flowchart's short class name ("Sensing I", and "Foundational" for Foundational Training), because the schedule's names ("Sensing I: Psychic and Consciousness Development") made titles unlike Daniel's. Found by running a real export through the page.
- The email and postal-address columns are found by name ("postal" first; an "address" column that says "email" is never the address), from the adversarial review.
- "Uploads are never stored" is enforced by `test_uploads_are_never_stored`, not a `verify: absent` line: the lint's absent check walks directories and passes silently on a single file.
- The branch was rebuilt on top of docs/digest-installed (PR #18) before the first commit, because both change NEXT-STEPS.md.
- Surface additions: `docs/memory/class-lists.md` and the rebuilt `docs/memory/MEMORY.md`.

## Why

Before every class Daniel turns a Corsizio attendee export (CSV, generic file name) into a formatted class list workbook. Until now that ran in a claude.ai chat, then in a local script, with names moved to Repeaters by hand each time. He wants it on the dashboard: upload the export, review it, download the finished file. Two formats: one for every class, and Foundational's own.

## Observed (2026-11-12)

- Standard format, from the September chat's workbooks and the October Sensing I-III and Karmic Intensive lists: title merged across B2:E2 (Aptos Narrow 18 bold, centred, medium box); row 3 `#`, Last Name, First Name, Email (Calibri 14 bold, medium box); numbered rows (Aptos Narrow 12), surname order; a merged "Repeaters" title row, then repeaters in surname order with numbering carrying on; medium outer border; column A width 3. A local rebuild of this layout reproduces all four October lists cell for cell (values, borders, merges) once given Daniel's hand moves.
- Foundational format, from the 2026-10-16 list: title in F2 (Verdana 11 bold); row 4 Last Name, First Name, Email, Phone, add1, add2, city, state, zip, country, Repeater (Verdana 12 bold, medium top); thin grid, medium left and right edges; first-timers in surname order, then repeaters in surname order with a yellow fill; only first-timers carry an address, split into parts and title-cased, country in capitals.
- Corsizio CSV shapes: First Name, Last Name, Email, then optionally Coupon Code, or Phone, a free-text postal address and "first time or repeater" answer (Foundational form). Some names arrive all lower case.
- Repeaters in Daniel's lists: everyone with a coupon (his rule, 2026-09-16, which covers personal discount codes as well as VHREPEATER), plus hand moves. Of the 26 people he listed as repeaters across the four October lists, 19 already have that class in their tags in `vortexhealing.db` (5 more attendees do too; they may have been tagged after attending). Counts only; checked outside the repository.
- `openpyxl` is not in the backend venv or either requirements file. `python-multipart` is in `requirements.txt` only.

## Assumed

- Exports stay small (tens of rows), so the browser can send the CSV text as JSON.
- Daniel's decisions 2026-11-12: review before download; addresses split by rules with misses flagged (no lookup of missing postcodes); tag-based repeater suggestions, untickable.

## Acceptance criteria

1. A "Class Lists" sidebar page takes a CSV and shows every attendee: name, email, Repeater and Remove tick boxes, and why each repeater was suggested (coupon code, form answer, or "done <class> in your records").
2. Picking a class from the schedule fills the title as `<Class> Class List <Month> <D> <YYYY> Daniel`; a non-generic file name fills it too; the title stays editable. Foundational (picked or in the title) selects the Foundational format; a toggle overrides.
3. Download returns `<title>.xlsx` in the chosen format, laid out as observed above, with the ticks applied.
4. Foundational first-timers get add1, add2, city, state, zip and country from the address line. An address that cannot be fully split keeps what was found, goes whole into add1 if nothing was, is highlighted in the file and listed on the page.
5. Coupon codes other than VHREPEATER are marked "check" on the page.
6. Nothing uploaded is written to disk or the database; the page works without LM Studio.

## Surface

- `backend/app/class_lists.py` (new): parse, repeater rules, address split, the two workbook writers
- `backend/app/api/class_lists.py` (new): `POST /api/class-lists/preview`, `POST /api/class-lists/build`
- `backend/main.py`: mount the router
- `backend/requirements.txt`, `backend/requirements-test.txt`: `openpyxl==3.1.5`
- `backend/tests/test_class_lists.py` (new)
- `frontend/src/pages/ClassLists.tsx` (new), `frontend/src/App.tsx`, `frontend/src/components/Navigation.tsx`
- `docs/ARCHITECTURE.md`, `docs/adr/0011-class-lists-built-not-stored.md`, `docs/adr/README.md`, this plan, `docs/sessions/session_<stamp>.md`, `NEXT-STEPS.md`

## Design

- **Logic in one module, `app/class_lists.py`**: pure functions, no database, so tests feed it invented CSV text. `parse(csv_text)` returns attendee dicts (name tidy, coupon, form answer, phone, address); `split_address(text)` returns the parts plus a list of misses; `build_standard(title, attendees)` and `build_foundational(title, attendees)` return xlsx bytes.
- **Address split by rules**: country from a known-name list at the end (default AUSTRALIA when an Australian state and postcode are found); state (NSW, VIC, QLD, WA, SA, TAS, ACT, NT) and four-digit postcode at the end; with commas, the part before the state is the city and earlier parts are add1/add2; without commas, the street ends at the last street-type word (Road, Rd, Street, Close, Drive...). Anything missing is a named miss.
- **Router, two stateless JSON calls**: `preview` takes `{filename, csv_text, class_id?}`, returns the suggested title, format, class and attendees with suggestions; `build` takes `{title, format, attendees}` (the ticked list) and streams the workbook. Tag suggestions use `class_for` and `completed_from_tags` (ADR-0006) against students matched by email.
- **CSV sent as JSON text, not a multipart upload**: avoids adding `python-multipart` to CI for one field.
- **New dependency `openpyxl`**: the only maintained pure-Python xlsx writer that does merges, borders and fills; the layouts need all three.
- **Page `ClassLists.tsx`**: file input read with `File.text()`, class picker from `GET /api/classes`, the review table, a Download button that turns the response into a blob link. Inline styles, plain elements, React Query v3, as `Tasks.tsx`.

## Test plan

- Unit (`test_class_lists.py`, invented names and addresses): standard layout (numbering continues into Repeaters, merges, outer border, no Repeaters section when none); Foundational layout (headers, first-timers then repeaters, yellow fill, repeaters without address, flagged address highlighted); coupon, form-answer and lowercase-name rules; `split_address` on comma, no-comma, missing-postcode, overseas and junk inputs; preview API (title from class pick and from file name, Foundational detection, tag suggestion with reason, non-repeater coupon flagged); build API (attachment name, ticks applied, removed people absent). Each test seen red by breaking its rule once.
- E2E: n/a (the frontend has no tests): open the page at `localhost:3000`, run one real export through it, compare with Daniel's October Sensing I list, check the console is clean. Real data stays outside the repository; record counts only.

## Records

- Architecture map delta: yes (layout row, flow 9, invariant "uploaded class lists are never stored" with a verify line).
- ADR: yes, 0011: class lists are built in memory and never stored; repeater rules (coupon, form answer, tag suggestion, Daniel's ticks) and the two formats.

## Cross-repo impact

None. The local `~/Documents/Class-List-Builder` script (outside this repository) is superseded; it stays until Daniel says otherwise.

## Grill-me pass (more than ten files)

1. Could a tag suggestion put a first-timer under Repeaters unnoticed? Recommended: it is shown with its reason and unticked in one click; the page lists it above the button. Accepted.
2. Should uploads be kept for audit? Recommended: no; the CSV is in Downloads and the workbook is the record. Accepted (ADR-0011).
3. Does adding `openpyxl` break CI? Recommended: add it to `requirements-test.txt` in the same commit; tests import only `app.class_lists` and the router. Accepted.
4. Address parsing for overseas first-timers? Recommended: country found, rest in add1, flagged; Daniel finishes it by hand. Accepted.

## Open questions

- Number the Foundational rows (a `#` column, as an October draft had)? Recommended: no, the 2026-10-16 list has none.

## BACKLOG

- (none yet)
