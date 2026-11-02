"""Zoom transcripts: download new ones from the account and file them beside the others.

The report API lists the account's meeting instances, six months back at most; each
instance's transcript comes from /meetings/{uuid}/transcript as WebVTT. One UUID gives one
transcript, and the manifest in zoom-import/ records every UUID ever downloaded, so a re-run,
or a file renamed since, never downloads twice. File names do not identify a transcript: the
first import saved some under two or three names. Markdown goes into the ZOOM_FOLDER teacher
folder, into the one indexed (non-underscore) subfolder whose transcripts share the topic, else
into _inbox/, which the indexer skips until Daniel sorts it. Standard library only.
"""
import base64
import csv
import datetime
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Callable, Optional

from app.core.config import settings
from handouts import transcripts_dir

API = "https://api.zoom.us/v2"
TOKEN_URL = "https://zoom.us/oauth/token"
IMPORT_DIR = "zoom-import"
MANIFEST = "transcripts_manifest.csv"
FIELDS = ["instance_start", "topic", "meeting_id", "uuid", "file", "bytes"]
INBOX = "_inbox"
MONTHS = 6  # how far back the report API goes
SEP = " — "  # em dash between stamp and topic, as in every transcript file name
NAMED = re.compile(r"^\d{4}-\d{2}-\d{2} \d{4,5}" + SEP + r"(.+?)(?: \(\d+\))?\.md$")
CUE_TIME = re.compile(r"^\d{2}:\d{2}:\d{2}\.\d{3} --> ")
SPEAKER = re.compile(r"^([^:]{1,40}): (.*)$")


class ZoomClient:
    """Server-to-Server OAuth: refreshes its token before the hour is up, backs off on 429."""

    def __init__(self, creds: dict):
        self.creds = creds
        self.token = None
        self.token_expiry = 0.0

    def _refresh_token(self) -> None:
        auth = base64.b64encode(f"{self.creds['client_id']}:{self.creds['client_secret']}".encode()).decode()
        url = f"{TOKEN_URL}?grant_type=account_credentials&account_id={urllib.parse.quote(self.creds['account_id'])}"
        req = urllib.request.Request(url, method="POST")
        req.add_header("Authorization", f"Basic {auth}")
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.load(resp)
        self.token = data["access_token"]
        self.token_expiry = time.time() + data.get("expires_in", 3600) - 300

    def _bearer(self) -> str:
        if not self.token or time.time() > self.token_expiry:
            self._refresh_token()
        return self.token

    def _open(self, url: str, timeout: int, retries: int = 4):
        for attempt in range(retries):
            req = urllib.request.Request(url)
            req.add_header("Authorization", f"Bearer {self._bearer()}")
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    return resp.read()
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    time.sleep(2 ** (attempt + 1))
                    continue
                if e.code == 401 and attempt == 0:
                    self._refresh_token()
                    continue
                raise
        raise RuntimeError(f"Zoom kept refusing {url.split('?')[0]}")

    def get_json(self, path: str, params: Optional[dict] = None) -> dict:
        qs = ("?" + urllib.parse.urlencode(params)) if params else ""
        return json.loads(self._open(f"{API}{path}{qs}", timeout=60))

    def download(self, url: str) -> bytes:
        return self._open(url, timeout=120)


def load_credentials() -> dict:
    if not settings.ZOOM_CREDENTIALS:
        raise SystemExit("Not set: ZOOM_CREDENTIALS. Add it to backend/.env (see backend/.env.example).")
    path = Path(settings.ZOOM_CREDENTIALS).expanduser()
    creds = json.loads(path.read_text(encoding="utf-8"))
    missing = [k for k in ("account_id", "client_id", "client_secret") if not creds.get(k)]
    if missing:
        raise SystemExit(f"{path.name} lacks {', '.join(missing)}")
    return creds


def _settings() -> "tuple[Path, str, str]":
    missing = [k for k in ("TRANSCRIPTS_DIR", "ZOOM_USER_ID", "ZOOM_FOLDER") if not getattr(settings, k)]
    if missing:
        raise SystemExit(f"Not set: {', '.join(missing)}. Add to backend/.env (see backend/.env.example).")
    return transcripts_dir(), settings.ZOOM_USER_ID, settings.ZOOM_FOLDER


def windows(today: datetime.date) -> "list[tuple[str, str]]":
    """Calendar-month (from, to) pairs back from today; the report API takes a month at a time."""
    out, d = [], today
    for _ in range(MONTHS):
        first = d.replace(day=1)
        out.append((first.isoformat(), d.isoformat()))
        d = first - datetime.timedelta(days=1)
    return out


def instances(client, user: str, today: datetime.date) -> "dict[str, tuple[str, str, object]]":
    """uuid -> (UTC start, topic, meeting id) for every meeting instance in the report window."""
    found = {}
    for frm, to in windows(today):
        token = ""
        while True:
            params = {"from": frm, "to": to, "page_size": 300}
            if token:
                params["next_page_token"] = token
            data = client.get_json(f"/report/users/{urllib.parse.quote(user)}/meetings", params)
            for m in data.get("meetings", []):
                found[m["uuid"]] = (m.get("start_time") or "", m.get("topic") or "untitled", m.get("id"))
            token = data.get("next_page_token") or ""
            if not token:
                break
    return found


def transcript_info(client, uuid: str) -> Optional[dict]:
    """The transcript's metadata, or None when the instance has none Zoom will hand over."""
    enc = urllib.parse.quote(urllib.parse.quote(uuid, safe=""), safe="")  # Zoom wants '/' and '=' encoded twice
    try:
        meta = client.get_json(f"/meetings/{enc}/transcript")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise
    if meta.get("can_download") is False or not meta.get("download_url"):
        return None
    return meta


def stamp(start: str) -> str:
    """'2026-08-05T02:32:31Z' -> '2026-08-05 0232': the UTC start, as the first import named files."""
    if not re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", start):
        return "undated"
    return f"{start[:10]} {start[11:13]}{start[14:16]}"


def safe_name(s: str, maxlen: int = 120) -> str:
    s = re.sub(r'[/\\:*?"<>|]', "-", s).strip()
    s = re.sub(r"\s+", " ", s)
    return s[:maxlen] or "untitled"


def parse_vtt(text: str) -> "list[tuple[Optional[str], str]]":
    """(speaker or None, caption text) for each cue."""
    lines = text.lstrip("﻿").splitlines()
    cues, i = [], 0
    while i < len(lines):
        if CUE_TIME.match(lines[i]):
            i += 1
            words = []
            while i < len(lines) and lines[i].strip():
                words.append(lines[i].strip())
                i += 1
            joined = " ".join(words)
            m = SPEAKER.match(joined)
            cues.append((m.group(1).strip(), m.group(2).strip()) if m else (None, joined))
        i += 1
    return cues


def to_markdown(title: str, cues: "list[tuple[Optional[str], str]]") -> str:
    """Consecutive captions from one speaker become one paragraph, prefixed with the name."""
    out = [f"# {title}", "", "- Source: Zoom cloud recording transcript", "", "---", ""]
    speaker, buf = None, []
    for who, text in cues + [(object(), "")]:  # a sentinel speaker flushes the last paragraph
        if who != speaker:
            if buf:
                out += [(f"**{speaker}:** " if speaker else "") + " ".join(buf), ""]
            speaker, buf = who, []
        buf.append(text)
    return "\n".join(out) + "\n"


def topics_by_folder(dest: Path) -> "dict[str, set[str]]":
    """Topic as it appears in file names (casefolded) -> the indexed subfolders holding it.

    Underscore folders (the inbox, set-asides, duplicates) are never targets: a topic parked in
    one would otherwise look ambiguous and send every new transcript of it to the inbox.
    """
    seen: dict = {}
    for f in dest.glob("*/*.md"):
        m = NAMED.match(f.name)
        if m and not f.parent.name.startswith("_"):
            seen.setdefault(m.group(1).casefold(), set()).add(f.parent.name)
    return seen


def destination(topic: str, seen: "dict[str, set[str]]") -> str:
    folders = seen.get(safe_name(topic).casefold(), set())
    return next(iter(folders)) if len(folders) == 1 else INBOX


def known_uuids(manifest: Path) -> "set[str]":
    if not manifest.exists():
        return set()
    with manifest.open(newline="", encoding="utf-8") as f:
        return {r["uuid"] for r in csv.DictReader(f) if r.get("uuid")}


def _free_names(folder: Path, vtt_dir: Path, base: str) -> "tuple[Path, Path]":
    """Markdown and .vtt paths for base that overwrite nothing; a clash adds ' (2)', ' (3)'..."""
    name, n = base, 2
    while (folder / f"{name}.md").exists() or (vtt_dir / f"{name}.vtt").exists():
        name, n = f"{base} ({n})", n + 1
    return folder / f"{name}.md", vtt_dir / f"{name}.vtt"


def sync(client=None, dry_run: bool = False, today: Optional[datetime.date] = None,
         out: Callable[[str], None] = print) -> dict:
    """Downloads every transcript in the report window whose UUID is not in the manifest."""
    root, user, folder = _settings()
    if client is None:
        client = ZoomClient(load_credentials())
    staging, dest = root / IMPORT_DIR, root / folder
    manifest = staging / MANIFEST
    have, seen = known_uuids(manifest), topics_by_folder(dest)
    found = instances(client, user, today or datetime.date.today())
    counts = {"listed": len(found), "new": 0, "already_had": 0, "unavailable": 0}
    for uuid, (start, topic, meeting_id) in sorted(found.items(), key=lambda kv: kv[1][0]):
        if uuid in have:
            counts["already_had"] += 1
            continue
        meta = transcript_info(client, uuid)
        if meta is None:
            counts["unavailable"] += 1
            continue
        topic = meta.get("meeting_topic") or topic
        sub = destination(topic, seen)
        md, vtt = _free_names(dest / sub, staging / "vtt", f"{stamp(start)}{SEP}{safe_name(topic)}")
        counts["new"] += 1
        if dry_run:
            out(f"  would download: {sub}/{md.name}")
            continue
        raw = client.download(meta["download_url"])
        vtt.parent.mkdir(parents=True, exist_ok=True)
        vtt.write_bytes(raw)
        cues = parse_vtt(raw.decode("utf-8", errors="replace"))
        if cues:
            md.parent.mkdir(parents=True, exist_ok=True)
            md.write_text(to_markdown(md.stem, cues), encoding="utf-8")
            if sub != INBOX:
                seen.setdefault(safe_name(topic).casefold(), set()).add(sub)
        new_manifest = not manifest.exists()
        with manifest.open("a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if new_manifest:
                w.writerow(FIELDS)
            w.writerow([start.replace("T", " ")[:16], topic, meeting_id or "", uuid, vtt.name, len(raw)])
        have.add(uuid)
        out(f"  downloaded: {sub}/{md.name}" if cues else f"  empty transcript kept as {vtt.name}")
    return counts
