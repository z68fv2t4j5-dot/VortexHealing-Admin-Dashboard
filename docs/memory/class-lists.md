---
name: class-lists
description: Class Lists page turns a Corsizio attendee CSV into Daniel's class list workbook (standard or Foundational); nothing uploaded is stored; design in ADR-0011
metadata:
  type: project
---

**Fact:** `/class-lists` previews an export (repeaters from coupon, form answer or class tags, each with its reason), takes Daniel's ticks and returns `<title>.xlsx`. Layouts and repeater rules are in `backend/app/class_lists.py`; nothing is written to disk or the database.

**Why:** the lists used to be made in a claude.ai chat, with repeaters moved by hand every time.

**Authority:** ADR-0011
