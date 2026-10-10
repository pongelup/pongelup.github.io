"""Keep the website's CV in sync with the CV Overleaf project.

Steps:
  1. git pull the CV Overleaf repo.
  2. If its commit differs from the one last published (assets/cv/source_commit.txt),
     or --force is given: compile main.tex with Tectonic in a scratch copy.
  3. Copy the PDF to assets/cv/Leandro_Pongeluppe_CV.pdf and set the "updated" month
     on the site from \\cvdate in the CV.
  4. Rebuild the site, commit, and push (if the repo has a remote).

Usage:  python sync_cv.py [--force] [--no-push]
Runs unattended from Windows Task Scheduler (task "Website CV Sync").
"""
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

SITE = Path(__file__).resolve().parent
CV_REPO = SITE.parent / "CV Overleaf"
TECTONIC = SITE.parents[2] / "Softwares" / "Claude Code" / "tectonic" / "tectonic.exe"
PDF_OUT = SITE / "assets" / "cv" / "Leandro_Pongeluppe_CV.pdf"
STAMP = SITE / "assets" / "cv" / "source_commit.txt"
LOG = SITE / "_review" / "sync_cv.log"


def log(msg):
    line = f"{datetime.now():%Y-%m-%d %H:%M:%S}  {msg}"
    print(line)
    LOG.parent.mkdir(exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def git(repo, *args, check=True):
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout.strip()


def set_updated(month):
    """Write the CV's month (e.g. 'October 2026') into the site content files."""
    cv_yml = SITE / "content" / "cv.yml"
    s = cv_yml.read_text(encoding="utf-8")
    s = re.sub(r'^cv_updated: ".*?"', f'cv_updated: "{month}"', s, flags=re.M)
    cv_yml.write_text(s, encoding="utf-8")
    # The Home CV button carries no date (Leo, 2026-10-10), so home.yml is not touched.


def main():
    force = "--force" in sys.argv
    push = "--no-push" not in sys.argv

    git(CV_REPO, "pull", "-q")
    head = git(CV_REPO, "rev-parse", "HEAD")
    last = STAMP.read_text().strip() if STAMP.exists() else ""
    if head == last and not force:
        log(f"CV unchanged ({head[:7]}); nothing to do")
        return

    log(f"CV commit {head[:7]} (last published {last[:7] or 'none'}); compiling")
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / "cv"
        shutil.copytree(CV_REPO, work, ignore=shutil.ignore_patterns(".git"))
        r = subprocess.run([str(TECTONIC), "--keep-logs", "--outdir", str(work), str(work / "main.tex")],
                           capture_output=True, text=True)
        pdf = work / "main.pdf"
        if r.returncode != 0 or not pdf.exists():
            log("COMPILE FAILED, site left unchanged:\n" + r.stderr[-3000:])
            sys.exit(1)
        shutil.copyfile(pdf, PDF_OUT)

    m = re.search(r"\\newcommand\{\\cvdate\}\{([^}]*)\}", (CV_REPO / "main.tex").read_text(encoding="utf-8"))
    if m:
        set_updated(m.group(1).strip())
    STAMP.write_text(head + "\n")

    subprocess.run([sys.executable, str(SITE / "build.py")], check=True, cwd=SITE)
    git(SITE, "add", "-A")
    if not git(SITE, "status", "--porcelain"):
        log("No site changes after rebuild")
        return
    git(SITE, "commit", "-q", "-m", f"Sync CV from Overleaf ({head[:7]})")
    log(f"Committed site with CV {head[:7]}")
    if push and git(SITE, "remote", check=False):
        git(SITE, "push", "-q", "origin", "main")
        log("Pushed to GitHub")


if __name__ == "__main__":
    main()
