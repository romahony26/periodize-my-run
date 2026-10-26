"""Put a tagged version on the Pi, check it works, and put the old one back if it does not.

  python tools/deploy.py                 # the version at the top of CHANGELOG.md
  python tools/deploy.py 2.10.0-beta.16 --dry-run
  python tools/deploy.py --skip-checks   # only when the checks have just been run by hand

Steps, in order, each of which stops the deploy if it fails:
  1. Before anything is sent: the tag exists and points at HEAD, the working tree is clean, CHANGELOG's top entry is this version,
     ruff is clean and the tests pass: a few fast ones for a beta, the full ./check.sh for production.
  2. The tag is unpacked into versions/<version> on the Pi and the database is copied to backups/.
  3. `versions/current` is switched and the service restarted.
  4. Smoke tests against the running service: it is active, /api/state answers as JSON with this version, the page and script
     are served, the state has what the interface needs, and the journal since the restart holds no traceback.
  5. If step 4 fails, `current` is set back to the previous version, the service restarted and checked again.
  6. The tests, which are not in git, are archived beside the app so a lost laptop does not lose them.
"""
import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import tarfile
import time

APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOST = "root@192.168.1.2"
BASE = "/home/dietpi/.periodize-my-run"
BETA_TESTS = ("test_engine", "test_gaps", "test_next_level", "test_jobs_flow", "test_references", "test_pinned", "test_properties")   # a few seconds
QUICK = BETA_TESTS      # kept under its old name for callers that still use it
NEEDED_KEYS = ("version", "days", "settings", "fitness", "readiness", "warnings", "scorecard", "season")


class Stop(Exception):
    pass


def run(cmd, text=True, **kw):
    return subprocess.run(cmd, capture_output=True, text=text, cwd=kw.pop("cwd", APP), **kw)  # noqa: S603, S607 - git, ssh and python, by name


def ssh(command, host=HOST, timeout=120):
    r = run(["ssh", "-o", "ConnectTimeout=15", host, command], stdin=subprocess.DEVNULL, timeout=timeout)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def changelog_top():
    with open(os.path.join(APP, "CHANGELOG.md"), encoding="utf-8") as f:
        m = re.search(r"^## (\S+) - \d{4}-\d{2}-\d{2}", f.read(), re.M)
    return m.group(1) if m else None


def vkey(v):
    core, _, beta = v.partition("-beta.")
    return (*(int(x) for x in core.split(".")), 0 if beta else 1, int(beta or 0))


def preflight(version, quick_tests=True):
    """Everything that can be known before anything is sent. Returns a list of what was checked, or raises Stop."""
    done = []
    if changelog_top() != version:
        raise Stop(f"CHANGELOG.md's top entry is {changelog_top()}, not {version}")
    done.append("changelog names this version")
    tag = run(["git", "rev-parse", f"v{version}^{{commit}}"])
    head = run(["git", "rev-parse", "HEAD"])
    if tag.returncode:
        raise Stop(f"tag v{version} does not exist")
    if tag.stdout.strip() != head.stdout.strip():
        raise Stop(f"tag v{version} is not at HEAD: commit what is pending and tag it")
    done.append("tag is at HEAD")
    if run(["git", "status", "--porcelain"]).stdout.strip():
        raise Stop("the working tree has uncommitted changes")
    done.append("working tree is clean")
    py = os.path.join(os.path.dirname(APP), ".venv", "bin", "python")
    if run([py, "-m", "ruff", "check", ".", "--quiet"]).returncode:
        raise Stop("ruff reports problems")
    done.append("ruff is clean")
    if quick_tests and "-beta" in version:          # a beta: ruff and a few fast tests
        for t in BETA_TESTS:
            r = run([py, "-W", "ignore", "-m", "unittest", f"tests.{t}"], env={**os.environ, "PYTHONPATH": f"{APP}:{APP}/tests"})
            if r.returncode:
                raise Stop(f"{t} failed:\n" + "\n".join(r.stderr.splitlines()[-12:]))
        done.append(f"{len(BETA_TESTS)} fast test files pass (a beta; production runs the full check)")
    elif quick_tests:                                # production: the full check, browser tests included
        r = run(["sh", os.path.join(APP, "check.sh")], timeout=1800)
        if r.returncode:
            raise Stop("the full check failed:\n" + "\n".join((r.stdout or "").splitlines()[-25:]))
        done.append("the full check passes (production)")
    return done


def smoke(version, host=HOST, since=None):
    """Checks against the running service on the Pi. Returns a list of problems (empty when it is healthy)."""
    problems = []
    code, out, _ = ssh("systemctl is-active periodize-my-run", host)
    if out != "active":
        return [f"service is {out or 'not answering'}"]
    time.sleep(1)
    for _ in range(8):      # the service is slow to answer for a while after a restart on the Pi: wait for it, up to about 80 seconds
        code, out, err = ssh("curl -sk --max-time 20 -H 'X-Requested-With: periodize' https://127.0.0.1:8321/api/state", host)
        if out:
            break
        time.sleep(10)
    try:
        state = json.loads(out)
    except ValueError:
        return [f"/api/state did not return JSON ({(out or err)[:80]!r})"]
    if state.get("version") != version:
        problems.append(f"/api/state reports version {state.get('version')}, expected {version}")
    missing = [k for k in NEEDED_KEYS if k not in state]
    if missing:
        problems.append(f"/api/state is missing {missing}")
    for path, needle in (("/", "periodize"), ("/static/app.js", "function render"), ("/static/plan.js", "function planView"), ("/static/boot.js", "load()")):
        code, out, _ = ssh(f"curl -sk --max-time 20 https://127.0.0.1:8321{path}", host)
        if needle not in out:
            problems.append(f"{path} did not serve what was expected")
    code, out, _ = ssh(f"journalctl -u periodize-my-run --since '{since or '2 minutes ago'}' --no-pager | grep -c -E 'Traceback|Unhandled error'", host)
    if out.strip() not in ("0", ""):
        problems.append(f"the journal holds {out.strip()} traceback(s) since the restart")
    return problems


def deploy(version, host=HOST, dry=False, skip_checks=False, out=print):
    steps = []
    if not skip_checks:
        steps += preflight(version)
    else:
        steps += ["checks skipped by request"]
    for s in steps:
        out(f"  ok  {s}")
    code, previous, _ = ssh(f"cat {BASE}/versions/current", host)
    if code:
        raise Stop("could not read the version now running on the Pi")
    out(f"  now running {previous}; deploying {version}")
    if vkey(version) < vkey(previous):
        out(f"  note: {version} is older than {previous}")
    if dry:
        out("  dry run: nothing was sent")
        return {"ok": True, "dry": True, "previous": previous}
    tarball = run(["git", "archive", f"v{version}"], text=False)
    if tarball.returncode:
        raise Stop("git archive failed")
    unpack = (f"set -e; mkdir -p {BASE}/versions/{version}; tar -x -C {BASE}/versions/{version}; chown -R dietpi:dietpi {BASE}/versions/{version}; "
              f"cp {BASE}/periodize.db {BASE}/backups/periodize-pre-{version}.db; chown dietpi:dietpi {BASE}/backups/periodize-pre-{version}.db")
    r = subprocess.run(["ssh", host, unpack], input=tarball.stdout, capture_output=True, timeout=300)  # noqa: S603, S607
    if r.returncode:
        raise Stop("unpacking on the Pi failed: " + r.stderr.decode()[:200])
    started = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() - 5))
    _, remote_now, _ = ssh("date '+%Y-%m-%d %H:%M:%S'", host)
    switch = f"printf '%s' {shlex.quote(version)} > {BASE}/versions/current; chown dietpi:dietpi {BASE}/versions/current; systemctl restart periodize-my-run; sleep 8"
    ssh(switch, host, timeout=90)
    problems = smoke(version, host, since=remote_now or started)
    if problems:
        out("  FAILED: " + "; ".join(problems))
        back = f"printf '%s' {shlex.quote(previous)} > {BASE}/versions/current; chown dietpi:dietpi {BASE}/versions/current; systemctl restart periodize-my-run; sleep 8"
        ssh(back, host, timeout=90)
        again = smoke(previous, host)
        out("  rolled back to " + previous + (" and it is healthy" if not again else " BUT IT IS NOT HEALTHY: " + "; ".join(again)))
        return {"ok": False, "previous": previous, "problems": problems, "rollback_healthy": not again}
    out(f"  ok  smoke tests pass on {version}")
    archive_tests(version, out)
    return {"ok": True, "previous": previous}


def archive_tests(version, out=print):
    """The tests are kept out of git by the project's own rule, so keep a copy beside the app."""
    src = os.path.join(APP, "tests")
    if not os.path.isdir(src):
        return None
    dest_dir = os.path.join(os.path.dirname(APP), "test-archive")
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, f"tests-{version}.tar.gz")
    with tarfile.open(dest, "w:gz") as t:
        t.add(src, arcname="tests", filter=lambda i: None if "__pycache__" in i.name or i.name.endswith(".pyc") or "/screenshots/" in i.name else i)
    for old in sorted(f for f in os.listdir(dest_dir) if f.startswith("tests-"))[:-8]:       # the last eight
        os.unlink(os.path.join(dest_dir, old))
    out(f"  ok  tests archived at {os.path.relpath(dest, os.path.dirname(APP))}")
    return dest


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("version", nargs="?")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--skip-checks", action="store_true")
    ap.add_argument("--host", default=HOST)
    a = ap.parse_args(argv)
    version = a.version or changelog_top()
    print(f"Deploying {version} to {a.host}")
    try:
        res = deploy(version, a.host, a.dry_run, a.skip_checks)
    except Stop as e:
        print("  STOPPED: " + str(e))
        return 2
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
