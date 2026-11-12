"""Class list workbooks from a Corsizio attendee export, in Daniel's two formats (ADR-0011).
Nothing here touches the database or the disk: CSV text in, xlsx bytes out."""
import csv
import io
import re
import unicodedata
from datetime import datetime
from typing import Optional

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

from app.class_rules import FOUNDATIONAL, class_for

# Corsizio names its exports like "20-attendees-export-68640df16963e9c1814a4535-2.csv"
GENERIC_EXPORT_NAME = re.compile(r"^\d+-attendees-export-[0-9a-f]+(-\d+)?$")
TRAILING_NOTE = re.compile(r"\s*\([^)]*\)$")  # "Magical Structures (November)" in the schedule
REPEATER_COUPON = "repeat"  # VHREPEATER; any other coupon still makes a repeater, but is marked for checking
TITLE_NAMES = {FOUNDATIONAL: "Foundational"}  # as Daniel titles it: "Foundational Class List ..."

ADDRESS_FIELDS = ("add1", "add2", "city", "state", "zip", "country")
AU_STATES = r"NSW|VIC|QLD|WA|SA|TAS|ACT|NT"
COUNTRIES = sorted([
    "australia", "new zealand", "the netherlands", "netherlands", "japan", "indonesia", "singapore", "malaysia",
    "thailand", "philippines", "hong kong", "china", "taiwan", "south korea", "korea", "india", "vietnam",
    "united kingdom", "uk", "england", "ireland", "germany", "france", "belgium", "switzerland", "austria",
    "spain", "portugal", "italy", "denmark", "sweden", "norway", "finland", "united states", "usa", "canada",
], key=len, reverse=True)
STREET_WORDS = {
    "road", "rd", "street", "st", "avenue", "ave", "drive", "dr", "close", "cl", "court", "ct", "crescent", "cres",
    "place", "pl", "lane", "ln", "way", "parade", "pde", "terrace", "tce", "highway", "hwy", "boulevard", "blvd",
    "grove", "circuit", "cct", "esplanade", "esp",
}


def tidy(text: str) -> str:
    """Collapse spaces; capitalise text typed all in lower or upper case, leave mixed case alone"""
    text = " ".join((text or "").split())
    return text.title() if text.islower() or text.isupper() else text


def _column(fields: list, needle: str, unless: str = "\0") -> Optional[str]:
    return next((f for f in fields if needle in f.lower() and unless not in f.lower()), None)


def parse(csv_text: str) -> list:
    """Attendees from a Corsizio export; repeaters marked from the coupon code or the first-time/repeater answer"""
    reader = csv.DictReader(io.StringIO(csv_text.lstrip("\ufeff")))
    fields = reader.fieldnames or []
    if "First Name" not in fields or "Last Name" not in fields:
        raise ValueError("This does not look like a Corsizio attendee export: no First Name and Last Name columns")
    coupon_col, answer_col = _column(fields, "coupon"), _column(fields, "repeater")
    email_col = "Email" if "Email" in fields else _column(fields, "email")
    phone_col = _column(fields, "phone")
    address_col = _column(fields, "postal") or _column(fields, "address", unless="email")
    attendees = []
    for row in reader:
        first, last = tidy(row.get("First Name")), tidy(row.get("Last Name"))
        if not (first or last):
            continue
        a = {"first": first, "last": last, "email": (row.get(email_col) or "").strip() if email_col else "",
             "phone": (row.get(phone_col) or "").strip() if phone_col else "",
             "address": " ".join((row.get(address_col) or "").split()) if address_col else "",
             "repeater": False, "reason": "", "check": False}
        coupon = (row.get(coupon_col) or "").strip() if coupon_col else ""
        answer = (row.get(answer_col) or "").strip() if answer_col else ""
        if coupon:
            a.update(repeater=True, reason=f"coupon {coupon}", check=REPEATER_COUPON not in coupon.lower())
        elif "repeat" in answer.lower():
            a.update(repeater=True, reason="answered Repeater on the form")
        attendees.append(a)
    return attendees


def split_address(text: str) -> tuple:
    """add1, add2, city, state, zip and country from a one-line address, and what could not be found.
    Rules: country at the end; an Australian state and four-digit postcode before it; with commas the part
    before the state is the suburb; without them the street ends at the first street word (Road, St...)."""
    parts = dict.fromkeys(ADDRESS_FIELDS, "")
    rest = " ".join((text or "").split()).strip(" ,.")
    if not rest:
        return parts, ["no address"]
    low = rest.lower()
    for name in COUNTRIES:
        if low.endswith(name) and (len(low) == len(name) or low[-len(name) - 1] in " ,"):
            parts["country"] = "NETHERLANDS" if name.endswith("netherlands") else name.upper()
            rest = rest[:-len(name)].rstrip(" ,.")
            break
    if parts["country"] in ("", "AUSTRALIA"):
        if m := re.search(r"(^|[,\s])(\d{4})$", rest):
            parts["zip"], rest = m.group(2), rest[:m.start()].rstrip(" ,.")
        if m := re.search(rf"(^|[,\s])({AU_STATES})$", rest, re.I):
            parts["state"], rest = m.group(2).upper(), rest[:m.start()].rstrip(" ,.")
        if (parts["zip"] or parts["state"]) and not parts["country"]:
            parts["country"] = "AUSTRALIA"
    elif rest:  # overseas: keep the lines together for Daniel to finish
        parts["add1"] = tidy(rest)
        return parts, ["overseas address: check the split"]

    chunks = [c.strip() for c in rest.split(",") if c.strip()]
    if len(chunks) >= 2:
        street, parts["city"] = chunks[:-1], chunks[-1]
        parts["add1"], parts["add2"] = street[0], ", ".join(street[1:])
    else:
        words = rest.split()
        # from the third word on, so the "St" of "12 St Georges Rd" is not taken for the street type
        at = next((i for i, w in enumerate(words) if i >= 2 and w.lower().strip(".") in STREET_WORDS), None)
        if at is None:
            parts["add1"] = rest
        else:
            parts["add1"], parts["city"] = " ".join(words[:at + 1]), " ".join(words[at + 1:])
    for key in ("add1", "add2", "city"):
        parts[key] = tidy(parts[key])

    misses = [label for key, label in (("city", "no suburb"), ("state", "no state"), ("zip", "no postcode"),
                                       ("country", "no country")) if not parts[key]]
    return parts, misses


def class_from_title(title: str) -> Optional[str]:
    """The flowchart class a title names: "Sensing I Class List October 3 2026 Daniel" -> "Sensing I" """
    name = re.split(r"\s+class\s+list\b|_class_list\b", title or "", maxsplit=1, flags=re.I)[0]
    return class_for(name.replace("_", " "))


def title_for(class_name: str, start: Optional[datetime]) -> str:
    """Daniel's title: "<Class> Class List <Month> <D> <YYYY> Daniel", with the flowchart's short class name
    ("Sensing I", not the schedule's "Sensing I: Psychic and Consciousness Development") where there is one"""
    cls = class_for(class_name or "")
    name = TITLE_NAMES.get(cls, cls) or TRAILING_NOTE.sub("", class_name or "").strip()
    when = f" {start.strftime('%B')} {start.day} {start.year}" if start else ""
    return f"{name} Class List{when} Daniel"


def title_from_filename(filename: str) -> str:
    """A renamed export carries its title; Corsizio's generic names do not"""
    stem = re.sub(r"\.csv$", "", (filename or "").strip(), flags=re.I)
    return "" if not stem or GENERIC_EXPORT_NAME.match(stem) else stem


def is_foundational(title: str, class_name: Optional[str] = None) -> bool:
    return FOUNDATIONAL in (class_from_title(title), class_for(class_name or "")) or "foundational" in title.lower()


def _sort_key(a: dict) -> tuple:
    def fold(s):
        return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().casefold()
    return fold(a["last"]), fold(a["first"])


def _ordered(attendees: list) -> tuple:
    return (sorted((a for a in attendees if not a["repeater"]), key=_sort_key),
            sorted((a for a in attendees if a["repeater"]), key=_sort_key))


def _box(col: int, first: int, last: int, side: Side, top=None, bottom=None) -> Border:
    """Inner cell border; the table's left and right edges are medium"""
    medium = Side(style="medium")
    return Border(left=medium if col == first else side, right=medium if col == last else side,
                  top=top if top is not None else side, bottom=bottom if bottom is not None else side)


def _save(wb: Workbook) -> bytes:
    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()


# Every class but Foundational: the layout of the September chat's lists and the October Sensing lists
STD_TITLE_FONT = Font(name="Aptos Narrow", size=18, bold=True)
STD_HEADER_FONT = Font(name="Calibri", size=14, bold=True)
STD_BODY_FONT = Font(name="Aptos Narrow", size=12)
CENTER = Alignment(horizontal="center", vertical="center")
LEFT = Alignment(horizontal="left", vertical="center")
STD_HEADERS = ("# ", "Last Name ", "First Name ", "Email ")
STD_MIN_WIDTHS = {"C": 12, "D": 13, "E": 30}


def build_standard(title: str, attendees: list) -> bytes:
    """Title, numbered attendees by surname, then a Repeaters title and the repeaters, numbering carried on"""
    main, repeaters = _ordered(attendees)
    everyone = main + repeaters
    first, last, medium, none = 2, 5, Side(style="medium"), Side()
    wb = Workbook()
    ws = wb.active
    ws.title = "Class List"

    def title_row(row, text):
        ws.merge_cells(start_row=row, start_column=first, end_row=row, end_column=last)
        cell = ws.cell(row, first, text)
        cell.font, cell.alignment = STD_TITLE_FONT, CENTER
        for col in range(first, last + 1):
            ws.cell(row, col).border = _box(col, first, last, none, top=medium, bottom=medium)
        ws.row_dimensions[row].height = 25

    def person_row(row, number, a):
        end = a is everyone[-1]
        for col, value in zip(range(first, last + 1), (number, a["last"], a["first"], a["email"])):
            cell = ws.cell(row, col, value)
            cell.font, cell.alignment = STD_BODY_FONT, LEFT
            cell.border = _box(col, first, last, none, bottom=medium if end else none)
        ws.row_dimensions[row].height = 18

    title_row(2, title)
    for col, text in zip(range(first, last + 1), STD_HEADERS):
        cell = ws.cell(3, col, text)
        cell.font, cell.alignment = STD_HEADER_FONT, LEFT
        cell.border = _box(col, first, last, none, top=medium, bottom=medium)
    ws.row_dimensions[3].height = 20

    row = 4
    for number, a in enumerate(main, 1):
        person_row(row, number, a)
        row += 1
    if repeaters:
        title_row(row, "Repeaters")
        row += 1
        for number, a in enumerate(repeaters, len(main) + 1):
            person_row(row, number, a)
            row += 1

    ws.column_dimensions["A"].width = 3
    ws.column_dimensions["B"].width = 8
    for letter, key, pad in (("C", "last", 3), ("D", "first", 3), ("E", "email", 2)):
        longest = max((len(a[key]) for a in everyone), default=0)
        ws.column_dimensions[letter].width = max(STD_MIN_WIDTHS[letter], longest + pad)
    return _save(wb)


# Foundational: the layout of the 2026-10-16 list, numbered (Daniel, 2026-11-12)
FND_TITLE_FONT = Font(name="Verdana", size=11, bold=True)
FND_HEADER_FONT = Font(name="Verdana", size=12, bold=True)
FND_BODY_FONT = Font(name="Verdana", size=12)
FND_HEADERS = ("#", "Last Name", "First Name", "Email", "Phone", "add1", "add2", "city", "state", "zip", "country",
               "Repeater")
FND_WIDTHS = {"A": 8, "B": 18.8, "C": 16, "D": 36, "E": 28.2, "F": 46, "G": 23.7, "H": 23.3, "I": 10, "J": 23.5,
              "K": 21.7, "L": 11.7}
REPEATER_FILL = PatternFill("solid", fgColor="FFFFFF00")  # yellow, as in Daniel's list
CHECK_FILL = PatternFill("solid", fgColor="FFF8CBAD")  # light orange: an address the rules could not fully split


def build_foundational(title: str, attendees: list) -> bytes:
    """First-timers by surname with their address split, then repeaters (yellow, no address), all numbered"""
    first_timers, repeaters = _ordered(attendees)
    everyone = first_timers + repeaters
    first, last, thin, medium = 1, 12, Side(style="thin"), Side(style="medium")
    wb = Workbook()
    ws = wb.active
    ws.title = "Class List"

    ws["F2"] = title
    ws["F2"].font = FND_TITLE_FONT
    for col, text in enumerate(FND_HEADERS, first):
        cell = ws.cell(4, col, text)
        cell.font = FND_HEADER_FONT
        cell.border = _box(col, first, last, thin, top=medium)

    for number, a in enumerate(everyone, 1):
        row = 4 + number
        parts, misses = split_address(a["address"]) if not a["repeater"] else (dict.fromkeys(ADDRESS_FIELDS, ""), [])
        values = (number, a["last"], a["first"], a["email"], a["phone"], *(parts[f] for f in ADDRESS_FIELDS),
                  "Yes" if a["repeater"] else "No")
        for col, value in enumerate(values, first):
            cell = ws.cell(row, col, value)
            cell.font = FND_BODY_FONT
            cell.border = _box(col, first, last, thin, bottom=medium if a is everyone[-1] else None)
            if col in (5, 10):  # phone and postcode stay text, so Excel keeps a leading 0
                cell.number_format = "@"
            if a["repeater"]:
                cell.fill = REPEATER_FILL
            elif misses and 6 <= col <= 11:
                cell.fill = CHECK_FILL

    for letter, width in FND_WIDTHS.items():
        ws.column_dimensions[letter].width = width
    for row in range(4, 5 + len(everyone)):
        ws.row_dimensions[row].height = 16
    return _save(wb)
