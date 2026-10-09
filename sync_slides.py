"""Keep the class slides on the Teaching page in sync with Leo's MGMT 6110 teaching folder.

Leo's rule: every semester the site shows the most recent PDFs from his teaching area.

Steps (deterministic, no AI):
  1. Scan the MGMT 6110 course folder (Teaching\\MBA Courses\\MBA - Leandro Pongeluppe\\Mgmt 6110):
     every "Class N - <Title>" folder (N >= 1) and "Z - Slides", top level only, for class decks named
     "MGMT 6110 Global Class N - <Case>....pdf". Skip names containing the words backup, old, or previous,
     and PDFs larger than 90 MB.
  2. For each class number keep the most recently modified deck.
  3. Copy it to assets/slides/MGMT6110_Class_NN_<Title>.pdf (only when the bytes differ).
  4. Rewrite the "slides:" list (and "slides_semester:") in content/teaching.yml. The semester of each deck
     comes from its modification date: Spring = Jan-May, Summer = Jun-Aug, Fall = Sep-Dec.
  5. If anything changed: rebuild, commit (only the slide files, teaching.yml, and teaching/index.html),
     and push, but only from branch main.

assets/slides/slides_manifest.json records which files this script manages. A managed copy that is no
longer referenced is removed from the repo; files it never created (older hand-placed copies) are left alone.

Optional overrides live in website_sync_config.yml under "slides:" (title_overrides by class number,
case_overrides by class number, course_dir relative to the "Assistant Professor" folder).

Usage:  python sync_slides.py [--dry-run] [--no-push]
Runs unattended from the "Website Monthly Sync" task (see README, Automation).
"""
import hashlib
import json
import re
import shutil
import subprocess
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("Missing package. Run:  python -m pip install pyyaml")

SITE = Path(__file__).resolve().parent
ASSISTANT_PROF = SITE.parents[1]                      # ...\Assistant Professor
DEFAULT_COURSE = Path("Teaching") / "MBA Courses" / "MBA - Leandro Pongeluppe" / "Mgmt 6110"
SLIDES_DIR = SITE / "assets" / "slides"
MANIFEST = SLIDES_DIR / "slides_manifest.json"
TEACHING_YML = SITE / "content" / "teaching.yml"
CONFIG = SITE / "website_sync_config.yml"
LOG = SITE / "_review" / "sync_slides.log"
MAX_BYTES = 90 * 1024 * 1024

CLASS_DIR_RE = re.compile(r"^Class (\d+) - (.+)$")
DECK_RE = re.compile(r"(?i)^MGMT ?6110 Global Class (\d+)\s*-\s*(.+)\.pdf$")
SKIP_RE = re.compile(r"(?i)\b(backup|old|previous)\b")


def log(msg):
    line = f"{datetime.now():%Y-%m-%d %H:%M:%S}  {msg}"
    print(line)
    LOG.parent.mkdir(exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def git(*args, check=True):
    r = subprocess.run(["git", "-C", str(SITE), *args], capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout.strip()


def load_config():
    if CONFIG.exists():
        with open(CONFIG, encoding="utf-8") as f:
            return (yaml.safe_load(f) or {}).get("slides") or {}
    return {}


def semester(dt):
    if dt.month <= 5:
        return f"Spring {dt.year}"
    if dt.month <= 8:
        return f"Summer {dt.year}"
    return f"Fall {dt.year}"


def semester_key(label):
    season, year = label.split()
    return (int(year), {"Spring": 1, "Summer": 2, "Fall": 3}[season])


def slug(text):
    t = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    t = re.sub(r"[^A-Za-z0-9]+", "_", t).strip("_")
    while len(t) > 60 and "_" in t:          # keep file names short: drop whole trailing words
        t = t.rsplit("_", 1)[0]
    while "_" in t and t.rsplit("_", 1)[1].lower() in {"and", "of", "the", "for", "in", "to", "a"}:
        t = t.rsplit("_", 1)[0]
    return t


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def yq(text):
    """Double-quoted YAML scalar."""
    return '"' + str(text).replace("\\", "\\\\").replace('"', '\\"') + '"'


def find_decks(course, cfg):
    """Return {class_number: info} with the most recent deck per class."""
    titles, candidates = {}, []
    for d in sorted(p for p in course.iterdir() if p.is_dir()):
        m = CLASS_DIR_RE.match(d.name)
        if m and int(m.group(1)) >= 1:
            titles[int(m.group(1))] = m.group(2).strip()
            candidates.extend(sorted(d.glob("*.pdf")))
    zslides = course / "Z - Slides"
    if zslides.is_dir():
        candidates.extend(sorted(zslides.glob("*.pdf")))

    best = {}
    for pdf in candidates:
        m = DECK_RE.match(pdf.name)
        if not m:
            continue
        if SKIP_RE.search(pdf.name):
            log(f"skip (backup/old/previous): {pdf.name}")
            continue
        size = pdf.stat().st_size
        if size > MAX_BYTES:
            log(f"skip (> 90 MB, {size / 1048576:.0f} MB): {pdf.name}")
            continue
        n = int(m.group(1))
        mtime = pdf.stat().st_mtime
        if n not in best or (mtime, pdf.name) > (best[n]["mtime"], best[n]["src"].name):
            best[n] = {"src": pdf, "mtime": mtime, "case_raw": m.group(2)}

    title_over = {int(k): v for k, v in (cfg.get("title_overrides") or {}).items()}
    case_over = {int(k): v for k, v in (cfg.get("case_overrides") or {}).items()}
    decks = {}
    for n in sorted(best):
        b = best[n]
        title = title_over.get(n) or titles.get(n)
        if not title:
            log(f"skip class {n}: no 'Class {n} - <Title>' folder and no title override")
            continue
        case = case_over.get(n) or re.sub(r"\s*\([^)]*\)", "", b["case_raw"]).strip()
        dt = datetime.fromtimestamp(b["mtime"])
        decks[n] = {
            "src": b["src"], "mtime": dt, "title": title, "case": case, "semester": semester(dt),
            "file": f"MGMT6110_Class_{n:02d}_{slug(title)}.pdf",
        }
    return decks


def render_slides_block(decks):
    lines = ["slides:"]
    for n, d in decks.items():
        lines.append(
            f"  - {{ url: {yq('/assets/slides/' + d['file'])}, title: {yq(f'Class {n}. ' + d['title'])}, "
            f"case: {yq(d['case'])}, semester: {yq(d['semester'])} }}"
        )
    return "\n".join(lines) + "\n"


def update_teaching_yml(text, decks, latest):
    """Replace the slides list and set slides_semester; everything else is left byte-for-byte."""
    block = render_slides_block(decks)
    new, k = re.subn(r"(?m)^slides:\n(?:[ \t]+.*\n)*", lambda _: block, text, count=1)
    if k == 0:
        raise RuntimeError("could not find a 'slides:' list in content/teaching.yml")
    sem_line = f"slides_semester: {yq(latest)}\n"
    if re.search(r"(?m)^slides_semester:", new):
        new = re.sub(r"(?m)^slides_semester:.*\n", lambda _: sem_line, new, count=1)
    else:
        new, k = re.subn(r"(?m)^(slides_intro:.*\n)", lambda m: m.group(1) + sem_line, new, count=1)
        if k == 0:
            raise RuntimeError("could not find 'slides_intro:' in content/teaching.yml")
    return new


def main():
    dry = "--dry-run" in sys.argv
    push = "--no-push" not in sys.argv
    cfg = load_config()
    course = ASSISTANT_PROF / (cfg.get("course_dir") or DEFAULT_COURSE)
    if not course.is_dir():
        log(f"ERROR: course folder not found: {course}")
        sys.exit(1)

    decks = find_decks(course, cfg)
    if not decks:
        log("ERROR: no class decks found; site left unchanged")
        sys.exit(1)
    latest = max((d["semester"] for d in decks.values()), key=semester_key)

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    new_manifest, copies = {}, []
    for n, d in decks.items():
        dest = SLIDES_DIR / d["file"]
        src_hash = sha256(d["src"])
        if not dest.exists() or sha256(dest) != src_hash:
            copies.append((d["src"], dest))
        new_manifest[str(n)] = {
            "file": d["file"], "source": str(d["src"].relative_to(ASSISTANT_PROF)).replace("\\", "/"),
            "source_modified": d["mtime"].strftime("%Y-%m-%d %H:%M"), "semester": d["semester"],
            "sha256": src_hash,
        }
    keep = {v["file"] for v in new_manifest.values()}
    stale = sorted({v["file"] for v in manifest.values()} - keep)
    legacy = sorted(p.name for p in SLIDES_DIR.glob("*.pdf")
                    if p.name not in keep and p.name not in {v["file"] for v in manifest.values()})

    old_yml = TEACHING_YML.read_text(encoding="utf-8")
    new_yml = update_teaching_yml(old_yml, decks, latest)

    for n, d in decks.items():
        log(f"class {n}: {d['src'].name} ({d['mtime']:%Y-%m-%d %H:%M}, {d['semester']}) -> {d['file']}")
    for src, dest in copies:
        log(f"{'would copy' if dry else 'copy'}: {src.name} -> assets/slides/{dest.name}")
    for f in stale:
        log(f"{'would remove' if dry else 'remove'} managed copy no longer used: assets/slides/{f}")
    for f in legacy:
        log(f"note: assets/slides/{f} is not managed by this script and no longer listed; left in place")
    yml_changed = new_yml != old_yml
    if yml_changed:
        log(f"{'would update' if dry else 'update'} content/teaching.yml (slides as of {latest})")

    if dry:
        log("dry run: nothing written")
        return
    if not copies and not stale and not yml_changed and json.dumps(manifest, sort_keys=True) == json.dumps(new_manifest, sort_keys=True):
        log(f"Slides unchanged ({len(decks)} decks, {latest}); nothing to do")
        return

    SLIDES_DIR.mkdir(parents=True, exist_ok=True)
    for src, dest in copies:
        shutil.copyfile(src, dest)
    for f in stale:
        if (SLIDES_DIR / f).exists():
            git("rm", "-q", "--cached", "--ignore-unmatch", f"assets/slides/{f}")
            (SLIDES_DIR / f).unlink()
    MANIFEST.write_text(json.dumps(new_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if yml_changed:
        TEACHING_YML.write_text(new_yml, encoding="utf-8", newline="\n")

    subprocess.run([sys.executable, str(SITE / "build.py")], check=True, cwd=SITE, capture_output=True)
    git("add", "-A", "--", "assets/slides", "content/teaching.yml", "teaching/index.html")
    if not git("diff", "--cached", "--name-only"):
        log("No site changes after rebuild")
        return
    git("commit", "-q", "-m", f"Sync class slides from the MGMT 6110 folder ({latest})")
    log(f"Committed {len(copies)} new or updated deck(s), slides as of {latest}")
    branch = git("rev-parse", "--abbrev-ref", "HEAD")
    if push and branch == "main" and git("remote", check=False):
        git("push", "-q", "origin", "main")
        log("Pushed to GitHub")
    elif push:
        log(f"Not pushed: on branch '{branch}' (only main is pushed)")


if __name__ == "__main__":
    main()
