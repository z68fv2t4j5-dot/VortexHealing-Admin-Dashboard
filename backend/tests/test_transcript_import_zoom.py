"""Zoom transcript import, against a fake Zoom (invented text only, ADR-0008 pattern)."""
import datetime
import json
import urllib.error
import urllib.parse

import pytest

from app.core.config import settings
from transcript_import import zoom
from transcript_import.__main__ import main

SEP = zoom.SEP
TODAY = datetime.date(2026, 11, 2)
VTT = b"""WEBVTT

1
00:00:01.000 --> 00:00:04.000
Gardener: Roses like the morning sun.

2
00:00:04.500 --> 00:00:07.000
Gardener: Water them at the roots.

3
00:00:07.500 --> 00:00:09.000
Student: What about winter?
"""
MEETINGS = [
    {"uuid": "old==", "start_time": "2026-06-05T10:00:31Z", "topic": "Garden Basics", "id": 1},
    {"uuid": "a/b+c==", "start_time": "2026-10-01T09:30:00Z", "topic": "Garden Basics", "id": 2},
    {"uuid": "pond", "start_time": "2026-10-02T09:30:00Z", "topic": "Pond Care", "id": 3},
    {"uuid": "open", "start_time": "2026-10-03T09:30:00Z", "topic": "Open Session", "id": 4},
    {"uuid": "gone", "start_time": "2026-10-04T09:30:00Z", "topic": "Hedge Talk", "id": 5},
    {"uuid": "locked", "start_time": "2026-10-05T09:30:00Z", "topic": "Hedge Talk", "id": 6},
]


class FakeZoom:
    """Pages the report in two halves; 'gone' has no transcript and 'locked' may not be downloaded."""

    def __init__(self):
        self.downloads = []

    def get_json(self, path, params=None):
        if path.startswith("/report/users/"):
            half = len(MEETINGS) // 2
            if params.get("next_page_token"):
                return {"meetings": MEETINGS[half:]}
            return {"meetings": MEETINGS[:half], "next_page_token": "p2"}
        uuid = urllib.parse.unquote(urllib.parse.unquote(path.split("/")[2]))
        if uuid == "gone":
            raise urllib.error.HTTPError(path, 404, "Not Found", {}, None)
        if uuid == "locked":
            return {"can_download": False, "download_url": "https://zoom.example/locked"}
        return {"can_download": True, "download_url": f"https://zoom.example/{uuid}"}

    def download(self, url):
        self.downloads.append(url)
        return VTT


@pytest.fixture
def library(tmp_path, monkeypatch):
    root = tmp_path / "transcripts"
    teacher = root / "Teacher"
    for sub, day, topic in [("Classes", "2026-01-05 1000", "Garden Basics"), ("Healing", "2026-01-06 0900", "Soil Care"),
                            ("Classes", "2026-01-07 0900", "Open Session"), ("Healing", "2026-01-08 0900", "Open Session")]:
        (teacher / sub).mkdir(parents=True, exist_ok=True)
        (teacher / sub / f"{day}{SEP}{topic}.md").write_text("# kept\n", encoding="utf-8")
    staging = root / "zoom-import"
    staging.mkdir()
    # Downloaded in the first import under a five-digit stamp; its file name matches nothing now.
    (staging / "transcripts_manifest.csv").write_text(
        "instance_start,topic,meeting_id,uuid,file,bytes\n"
        f"2026-06-05 10:00,Garden Basics,1,old==,2026-06-05 10003{SEP}Garden Basics.vtt,10\n", encoding="utf-8")
    monkeypatch.setattr(settings, "TRANSCRIPTS_DIR", str(root))
    monkeypatch.setattr(settings, "ZOOM_USER_ID", "someone@example.com")
    monkeypatch.setattr(settings, "ZOOM_FOLDER", "Teacher")
    return root


def quiet(_):
    pass


def tree(root):
    return sorted((str(p.relative_to(root)), p.stat().st_size if p.is_file() else -1) for p in root.rglob("*"))


def test_new_transcripts_are_downloaded_converted_and_filed(library):
    fake = FakeZoom()
    counts = zoom.sync(client=fake, today=TODAY, out=quiet)
    assert counts == {"listed": 6, "new": 3, "already_had": 1, "unavailable": 2}
    teacher = library / "Teacher"
    filed = teacher / "Classes" / f"2026-10-01 0930{SEP}Garden Basics.md"
    assert filed.read_text(encoding="utf-8").splitlines()[0] == f"# 2026-10-01 0930{SEP}Garden Basics"
    assert "**Gardener:** Roses like the morning sun. Water them at the roots.\n\n**Student:** What about winter?" \
        in filed.read_text(encoding="utf-8")
    # Unknown topic, and a topic held by two folders: both wait in the inbox.
    assert (teacher / "_inbox" / f"2026-10-02 0930{SEP}Pond Care.md").exists()
    assert (teacher / "_inbox" / f"2026-10-03 0930{SEP}Open Session.md").exists()
    assert (library / "zoom-import" / "vtt" / f"2026-10-01 0930{SEP}Garden Basics.vtt").read_bytes() == VTT
    assert zoom.known_uuids(library / "zoom-import" / "transcripts_manifest.csv") == {"old==", "a/b+c==", "pond", "open"}
    # The UUID downloaded in the first import is not fetched again under a new name.
    assert not list(teacher.rglob("2026-06-05*"))
    assert "https://zoom.example/old==" not in fake.downloads


def test_second_run_downloads_nothing(library):
    zoom.sync(client=FakeZoom(), today=TODAY, out=quiet)
    fake = FakeZoom()
    counts = zoom.sync(client=fake, today=TODAY, out=quiet)
    assert counts == {"listed": 6, "new": 0, "already_had": 4, "unavailable": 2}
    assert fake.downloads == []


def test_dry_run_writes_nothing(library):
    before = tree(library)
    fake = FakeZoom()
    lines = []
    counts = zoom.sync(client=fake, dry_run=True, today=TODAY, out=lines.append)
    assert counts["new"] == 3 and fake.downloads == []
    assert tree(library) == before
    assert f"  would download: Classes/2026-10-01 0930{SEP}Garden Basics.md" in lines


def test_underscore_folders_are_never_targets(library):
    # A set-aside copy of a filed topic must not make it ambiguous, and a set-aside topic is not filed.
    parked = library / "Teacher" / "_duplicates"
    parked.mkdir()
    (parked / f"2026-01-09 0900{SEP}Garden Basics.md").write_text("# copy\n", encoding="utf-8")
    (parked / f"2026-01-10 0900{SEP}Pond Care.md").write_text("# copy\n", encoding="utf-8")
    zoom.sync(client=FakeZoom(), today=TODAY, out=quiet)
    assert (library / "Teacher" / "Classes" / f"2026-10-01 0930{SEP}Garden Basics.md").exists()
    assert (library / "Teacher" / "_inbox" / f"2026-10-02 0930{SEP}Pond Care.md").exists()


def test_an_existing_file_is_never_overwritten(library):
    kept = library / "Teacher" / "Classes" / f"2026-10-01 0930{SEP}Garden Basics.md"
    kept.write_text("# someone else's file\n", encoding="utf-8")
    zoom.sync(client=FakeZoom(), today=TODAY, out=quiet)
    assert kept.read_text(encoding="utf-8") == "# someone else's file\n"
    assert (library / "Teacher" / "Classes" / f"2026-10-01 0930{SEP}Garden Basics (2).md").exists()


def test_captions_merge_by_speaker():
    cues = zoom.parse_vtt("﻿" + VTT.decode() + "\n4\n00:00:09.500 --> 00:00:10.000\nno speaker here\n")
    assert cues[-1] == (None, "no speaker here")
    md = zoom.to_markdown("t", cues)
    assert md.endswith("**Student:** What about winter?\n\nno speaker here\n\n")


def test_stamp_is_the_utc_start_in_hhmm():
    assert zoom.stamp("2026-08-05T02:32:31Z") == "2026-08-05 0232"
    assert zoom.stamp("") == "undated"


def test_report_windows_reach_back_six_months():
    w = zoom.windows(TODAY)
    assert len(w) == 6 and w[0] == ("2026-11-01", "2026-11-02") and w[-1] == ("2026-06-01", "2026-06-30")


def test_missing_settings_stop_the_run_and_name_themselves(library, monkeypatch):
    monkeypatch.setattr(settings, "ZOOM_FOLDER", None)
    with pytest.raises(SystemExit, match="ZOOM_FOLDER"):
        zoom.sync(client=FakeZoom(), today=TODAY, out=quiet)
    monkeypatch.setattr(settings, "ZOOM_FOLDER", "Teacher")
    monkeypatch.setattr(settings, "ZOOM_CREDENTIALS", None)
    with pytest.raises(SystemExit, match="ZOOM_CREDENTIALS") as e:
        main(["zoom"])
    assert e.value.code  # a message, so the exit status is 1


def test_cli_dry_run_reads_credentials_and_prints_counts(library, monkeypatch, tmp_path, capsys):
    creds = tmp_path / "creds.json"
    creds.write_text(json.dumps({"account_id": "a", "client_id": "b", "client_secret": "c"}), encoding="utf-8")
    monkeypatch.setattr(settings, "ZOOM_CREDENTIALS", str(creds))
    monkeypatch.setattr(zoom, "ZoomClient", lambda c: FakeZoom() if c["client_id"] == "b" else None)
    main(["zoom", "--dry-run"])
    assert "listed: 6; would download: 3; already had: 1; unavailable: 2" in capsys.readouterr().out
    creds.write_text(json.dumps({"account_id": "a"}), encoding="utf-8")
    with pytest.raises(SystemExit, match="client_id, client_secret"):
        main(["zoom"])
