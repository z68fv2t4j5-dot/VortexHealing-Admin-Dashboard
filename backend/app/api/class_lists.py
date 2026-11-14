"""Class Lists page: a Corsizio export in, a reviewed class list workbook out. Nothing is stored (ADR-0011)."""
import re
from typing import List, Literal, Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import class_lists
from app.class_rules import class_for, completed_from_tags
from app.core.database import get_db
from app.models import Class, Student

router = APIRouter()
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


class PreviewRequest(BaseModel):
    filename: str = ""
    csv_text: str
    class_id: Optional[int] = None


class Attendee(BaseModel):
    first: str
    last: str
    email: str = ""
    phone: str = ""
    address: str = ""
    repeater: bool = False


class BuildRequest(BaseModel):
    title: str
    format: Literal["standard", "foundational"]
    attendees: List[Attendee]


@router.post("/class-lists/preview")
async def preview(req: PreviewRequest, db: Session = Depends(get_db)):
    """Attendees with suggested repeaters, a suggested title and format; the page lets Daniel change all three"""
    try:
        attendees = class_lists.parse(req.csv_text)
    except (ValueError, UnicodeError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not attendees:
        raise HTTPException(status_code=400, detail="No attendees found in this file")

    picked = db.query(Class).filter(Class.id == req.class_id).first() if req.class_id else None
    if req.class_id and not picked:
        raise HTTPException(status_code=404, detail="Class not found")
    title = class_lists.title_for(picked.name, picked.start_date) if picked else \
        class_lists.title_from_filename(req.filename)
    cls = class_for(picked.name) if picked else class_lists.class_from_title(title)

    if cls:  # suggest anyone whose class tags (ADR-0006) say they have done this class already
        emails = {a["email"].lower() for a in attendees if a["email"]}
        students = db.query(Student).filter(func.lower(Student.email).in_(emails)).all() if emails else []
        done = {s.email.lower() for s in students if cls in completed_from_tags(s.tags, s.lists)}
        for a in attendees:
            if not a["repeater"] and a["email"].lower() in done:
                a.update(repeater=True, reason=f"done {cls} in your records")

    for a in attendees:
        a["address_misses"] = class_lists.split_address(a["address"])[1] if a["address"] else []
    has_addresses = any(a["address"] for a in attendees)  # only the Foundational form asks for a postal address
    return {"title": title, "class_name": cls,
            "format": "foundational" if has_addresses or class_lists.is_foundational(title, cls) else "standard",
            "attendees": attendees}


@router.post("/class-lists/build")
async def build(req: BuildRequest):
    """The workbook for the reviewed list, as a download named after the title"""
    title = " ".join(req.title.split())
    if not title:
        raise HTTPException(status_code=400, detail="The class list needs a title")
    if not req.attendees:
        raise HTTPException(status_code=400, detail="Nobody is left on the list")
    attendees = [a.model_dump() for a in req.attendees]
    builder = class_lists.build_foundational if req.format == "foundational" else class_lists.build_standard
    filename = re.sub(r'[\\/:*?"<>|]', "-", title) + ".xlsx"
    return Response(builder(title, attendees), media_type=XLSX,
                    headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"})
