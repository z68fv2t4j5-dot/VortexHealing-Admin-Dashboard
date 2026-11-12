"""Class list workbooks. Every name, email and address here is invented (the repository is public)."""
import inspect
import io
import re
from datetime import datetime
from urllib.parse import unquote

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from openpyxl import load_workbook

from app import class_lists as cl
from app.api import class_lists as cl_api
from app.class_rules import FOUNDATIONAL
from app.core.database import get_db
from app.models import Class

COUPON_CSV = """\ufeffFirst Name,Last Name,Email,Coupon Code
Ivy,Jones,ivy@example.com,
Lou,Kane,lou@example.com,VHREPEATER
Greg,Stone,greg@example.com,GREG50
nara,soe,nara@example.com,
Ana,One,ana@example.com,
"""

FORM_CSV = '''"First Name","Last Name","Email","Phone","Enter your complete Postal Address, including country and postal code","Are you taking this workshop for the first time or as a repeater ?"
"Wren","Hill","wren@example.com","0400000001","12 Example Road, Sample Vale, NSW, 2474, Australia","First Time"
"Ada","Moss","ada@example.com","0400000002","Jane Doe","First Time"
"Bo","Yates","bo@example.com","0400000003","1 Test St Testville QLD 4000","Repeater"
'''


def rows(xlsx: bytes, min_col: int, max_col: int, min_row: int = 2) -> list:
    ws = load_workbook(io.BytesIO(xlsx)).active
    return [r for r in ws.iter_rows(min_row=min_row, min_col=min_col, max_col=max_col, values_only=True) if any(r)]


def person(last, first="X", repeater=False, address="", email="x@example.com", phone=""):
    return {"first": first, "last": last, "email": email, "phone": phone, "address": address, "repeater": repeater}


# --- parsing and repeater rules

def test_coupon_holders_are_repeaters_and_other_coupons_are_marked_for_checking():
    by_last = {a["last"]: a for a in cl.parse(COUPON_CSV)}
    assert (by_last["Kane"]["repeater"], by_last["Kane"]["reason"], by_last["Kane"]["check"]) == \
        (True, "coupon VHREPEATER", False)
    assert (by_last["Stone"]["repeater"], by_last["Stone"]["check"]) == (True, True)
    assert by_last["Jones"]["repeater"] is False


def test_names_typed_in_lower_case_are_capitalised():
    assert ("Nara", "Soe") in {(a["first"], a["last"]) for a in cl.parse(COUPON_CSV)}


def test_the_form_answer_marks_repeaters_and_brings_phone_and_address():
    bo = next(a for a in cl.parse(FORM_CSV) if a["last"] == "Yates")
    assert (bo["repeater"], bo["reason"], bo["phone"], bo["address"]) == \
        (True, "answered Repeater on the form", "0400000003", "1 Test St Testville QLD 4000")


def test_an_email_address_column_is_read_as_the_email_never_as_the_postal_address():
    a = cl.parse("First Name,Last Name,Email Address,Home Address\nIvy,Jones,ivy@example.com,1 Test St Testville\n")[0]
    assert (a["email"], a["address"]) == ("ivy@example.com", "1 Test St Testville")


def test_a_file_without_name_columns_is_refused():
    with pytest.raises(ValueError, match="Corsizio"):
        cl.parse("Name,Email\nIvy,ivy@example.com\n")


# --- address split

@pytest.mark.parametrize("text, parts, misses", [
    ("64 Example Avenue,  Middle Town, WA.  6054", ("64 Example Avenue", "", "Middle Town", "WA", "6054", "AUSTRALIA"), []),
    ("12 Example Road, Sample Vale, NSW, 2474, Australia", ("12 Example Road", "", "Sample Vale", "NSW", "2474", "AUSTRALIA"), []),
    ("19 white gum close redhill nsw 2290 Australia", ("19 White Gum Close", "", "Redhill", "NSW", "2290", "AUSTRALIA"), []),
    ("1/37 Sample Drive Mount Example QLD 4573 Australia", ("1/37 Sample Drive", "", "Mount Example", "QLD", "4573", "AUSTRALIA"), []),
    ("12 Smith St St Kilda VIC 3182", ("12 Smith St", "", "St Kilda", "VIC", "3182", "AUSTRALIA"), []),
    ("12 St Georges Rd Penshurst NSW 2222", ("12 St Georges Rd", "", "Penshurst", "NSW", "2222", "AUSTRALIA"), []),
    ("Unit 3, 12 Long Street, Newtown, NSW 2042", ("Unit 3", "12 Long Street", "Newtown", "NSW", "2042", "AUSTRALIA"), []),
    ("393 Example Rd Exampleton", ("393 Example Rd", "", "Exampleton", "", "", ""), ["no state", "no postcode", "no country"]),
    ("Kleine Laan 32 1435 GP Dorp The Netherlands", ("Kleine Laan 32 1435 GP Dorp", "", "", "", "", "NETHERLANDS"),
     ["overseas address: check the split"]),
    ("Jane Doe", ("Jane Doe", "", "", "", "", ""), ["no suburb", "no state", "no postcode", "no country"]),
    ("", ("", "", "", "", "", ""), ["no address"]),
])
def test_split_address(text, parts, misses):
    got, got_misses = cl.split_address(text)
    assert (tuple(got[f] for f in cl.ADDRESS_FIELDS), got_misses) == (parts, misses)


# --- titles and format

def test_titles_come_from_the_schedule_or_a_renamed_file():
    assert cl.title_for("Magical Structures (November)", datetime(2027, 11, 10, 13, 30)) == \
        "Magical Structures Class List November 10 2027 Daniel"
    assert cl.title_for("Sensing I: Psychic and Consciousness Development (September)", datetime(2027, 9, 11)) == \
        "Sensing I Class List September 11 2027 Daniel"
    assert cl.title_for("Foundational Training (May)", datetime(2027, 5, 12)) == \
        "Foundational Class List May 12 2027 Daniel"
    assert cl.title_for("Connecting with Quinstel (Asia Dec)", None) == "Connecting with Quinstel Class List Daniel"
    assert cl.title_from_filename("20-attendees-export-68640df16963e9c1814a4535-2.csv") == ""
    assert cl.title_from_filename("Sensing I Class List October 3 2026 Daniel.csv") == \
        "Sensing I Class List October 3 2026 Daniel"


def test_the_class_is_read_from_the_title_and_foundational_has_its_own_format():
    assert cl.class_from_title("Sensing I Class List October 3 2026 Daniel") == "Sensing I"
    assert cl.class_from_title("Foundational_Class_List Oct 23rd 2026 Daniel") == FOUNDATIONAL
    assert cl.is_foundational("Foundational Class List November 4 2026 Daniel")
    assert not cl.is_foundational("Sensing I Class List October 3 2026 Daniel")


# --- standard workbook

def test_standard_list_numbers_into_the_repeaters_section():
    xlsx = cl.build_standard("Sensing I Class List October 3 2026 Daniel", [
        person("Zed", "Amy"), person("Kane", "Lou", repeater=True), person("Ávila", "Jo"), person("Abel", "Max", True)])
    assert rows(xlsx, 2, 5) == [
        ("Sensing I Class List October 3 2026 Daniel", None, None, None),
        ("# ", "Last Name ", "First Name ", "Email "),
        (1, "Ávila", "Jo", "x@example.com"),
        (2, "Zed", "Amy", "x@example.com"),
        ("Repeaters", None, None, None),
        (3, "Abel", "Max", "x@example.com"),
        (4, "Kane", "Lou", "x@example.com"),
    ]


def test_standard_list_borders_and_merges():
    ws = load_workbook(io.BytesIO(cl.build_standard("T", [person("A"), person("B", repeater=True)]))).active
    assert sorted(map(str, ws.merged_cells.ranges)) == ["B2:E2", "B5:E5"]
    for row in (2, 3, 5):  # title, header, Repeaters
        assert all(ws.cell(row, c).border.top.style == "medium" for c in range(2, 6))
        assert all(ws.cell(row, c).border.bottom.style == "medium" for c in range(2, 6))
    assert all(ws.cell(r, 2).border.left.style == "medium" and ws.cell(r, 5).border.right.style == "medium"
               for r in range(2, 7))
    assert ws.cell(4, 3).border.bottom.style is None
    assert ws.cell(6, 3).border.bottom.style == "medium"
    assert (ws.cell(2, 2).font.size, ws.cell(2, 2).font.b, ws.cell(4, 3).font.name) == (18, True, "Aptos Narrow")


def test_standard_list_without_repeaters_has_no_repeaters_section():
    ws = load_workbook(io.BytesIO(cl.build_standard("T", [person("A"), person("B")]))).active
    assert [str(r) for r in ws.merged_cells.ranges] == ["B2:E2"]
    assert ws.max_row == 5 and ws.cell(5, 3).border.bottom.style == "medium"


# --- Foundational workbook

def test_foundational_list_puts_first_timers_with_addresses_then_repeaters_numbered():
    xlsx = cl.build_foundational("Foundational Class List November 4 2026 Daniel", [
        person("Yates", "Bo", repeater=True, address="1 Test St Testville QLD 4000"),
        person("Hill", "Wren", address="12 Example Road, Sample Vale, NSW, 2474, Australia", phone="0400000001")])
    ws = load_workbook(io.BytesIO(xlsx)).active
    assert ws["F2"].value == "Foundational Class List November 4 2026 Daniel"
    assert rows(xlsx, 1, 12, min_row=4) == [
        ("#", "Last Name", "First Name", "Email", "Phone", "add1", "add2", "city", "state", "zip", "country", "Repeater"),
        (1, "Hill", "Wren", "x@example.com", "0400000001", "12 Example Road", None, "Sample Vale", "NSW", "2474",
         "AUSTRALIA", "No"),
        (2, "Yates", "Bo", "x@example.com", None, None, None, None, None, None, None, "Yes"),
    ]
    assert ws["E5"].number_format == "@" and ws["J5"].number_format == "@"


def test_foundational_list_marks_repeaters_yellow_and_unsplit_addresses_orange():
    ws = load_workbook(io.BytesIO(cl.build_foundational("F", [
        person("Moss", address="Jane Doe"), person("Hill", address="12 Example Road, Sample Vale, NSW, 2474"),
        person("Yates", repeater=True)]))).active
    fill = lambda ref: ws[ref].fill.fgColor.rgb if ws[ref].fill.fill_type == "solid" else None
    assert fill("A7") == fill("L7") == "FFFFFF00"  # Yates, the repeater
    assert fill("F6") == fill("K6") == "FFF8CBAD" and fill("B6") is None  # Moss: address not split
    assert fill("F5") is None  # Hill: split cleanly
    assert ws["A4"].border.left.style == "medium" and ws["L4"].border.right.style == "medium"
    assert ws["A4"].border.top.style == "medium" and ws["C5"].border.bottom.style == "thin"
    assert ws["C7"].border.bottom.style == "medium"
    assert (ws["F2"].font.name, ws["B5"].font.name, ws["B4"].font.b) == ("Verdana", "Verdana", True)


# --- API

@pytest.fixture
def api(db):
    db.add_all([Class(id=10, name="Sensing I (Asia)", start_date=datetime(2026, 12, 13, 10, 0)),
                Class(id=11, name="Foundational", start_date=datetime(2026, 11, 4, 9, 0))])
    db.commit()
    app = FastAPI()
    app.include_router(cl_api.router, prefix="/api")
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app)


def test_preview_takes_the_title_from_the_picked_class_and_suggests_repeaters_from_tags(api):
    body = api.post("/api/class-lists/preview", json={"filename": "5-attendees-export-abc123.csv",
                                                      "csv_text": COUPON_CSV, "class_id": 10}).json()
    assert (body["title"], body["class_name"], body["format"]) == \
        ("Sensing I Class List December 13 2026 Daniel", "Sensing I", "standard")
    by_last = {a["last"]: a for a in body["attendees"]}
    assert (by_last["One"]["repeater"], by_last["One"]["reason"]) == (True, "done Sensing I in your records")
    assert by_last["Stone"]["check"] is True and by_last["Jones"]["repeater"] is False


def test_preview_of_a_renamed_foundational_file_picks_the_foundational_format(api):
    csv_text = FORM_CSV + '"Cal","Three","cal@example.com","0400000004","","First Time"\n'
    body = api.post("/api/class-lists/preview", json={
        "filename": "Foundational Class List November 4 2026 Daniel.csv", "csv_text": csv_text}).json()
    by_last = {a["last"]: a for a in body["attendees"]}
    assert (body["title"], body["format"]) == ("Foundational Class List November 4 2026 Daniel", "foundational")
    assert by_last["Three"]["reason"] == f"done {FOUNDATIONAL} in your records"  # on the APAC Wizards list
    assert by_last["Moss"]["address_misses"] == ["no suburb", "no state", "no postcode", "no country"]
    assert by_last["Hill"]["address_misses"] == []


def test_preview_refuses_a_file_that_is_not_an_export_and_an_unknown_class(api):
    assert api.post("/api/class-lists/preview", json={"csv_text": "Name\nIvy\n"}).status_code == 400
    assert api.post("/api/class-lists/preview", json={"csv_text": COUPON_CSV, "class_id": 99}).status_code == 404


def test_build_returns_the_ticked_list_as_a_download_named_after_the_title(api):
    res = api.post("/api/class-lists/build", json={
        "title": "Sensing I Class List December 13 2026 Daniel", "format": "standard",
        "attendees": [person("Jones", "Ivy"), person("Kane", "Lou", repeater=True)]})
    assert res.status_code == 200
    assert unquote(res.headers["content-disposition"]).endswith("Sensing I Class List December 13 2026 Daniel.xlsx")
    assert [r[1] for r in rows(res.content, 2, 5)[2:]] == ["Jones", None, "Kane"]


def test_build_in_the_foundational_format(api):
    res = api.post("/api/class-lists/build", json={"title": "F", "format": "foundational",
                                                   "attendees": [person("Hill")]})
    assert load_workbook(io.BytesIO(res.content)).active["B4"].value == "Last Name"


def test_uploads_are_never_stored():
    """ADR-0011: the module has no database or file access, and the router only reads students and classes"""
    assert not re.search(r"\bopen\(|app\.core\.database|Session|\.write", inspect.getsource(cl))
    assert not re.search(r"\.add\(|\.add_all\(|\.commit\(|\.delete\(|\bopen\(|\.write", inspect.getsource(cl_api))


def test_build_refuses_an_empty_title_or_an_empty_list(api):
    assert api.post("/api/class-lists/build", json={"title": " ", "format": "standard",
                                                    "attendees": [person("A")]}).status_code == 400
    assert api.post("/api/class-lists/build", json={"title": "T", "format": "standard",
                                                    "attendees": []}).status_code == 400
