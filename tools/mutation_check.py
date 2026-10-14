"""Do the tests notice when a rule is changed? Make small changes to the planner's source, one at a time, and see whether any test fails.

  python tools/mutation_check.py [--files engine.py,insights.py] [--n 60] [--seed 1]

Each "mutant" changes one comparison (< to <=, > to >=, == to !=) or one number (by about 10%) in a copy of the app, then runs the fast
tests. A mutant that no test notices "survived": either the line is not tested, or the change makes no difference. Survivors are listed so
each can be looked at; the score is the share killed. This is a sample, not the whole space.
"""
import argparse
import ast
import os
import random
import shutil
import subprocess
import sys
import tempfile
import time

APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = os.path.join(os.path.dirname(APP), ".venv", "bin", "python")
FAST = ["tests.test_engine", "tests.test_gaps", "tests.test_next_level", "tests.test_jobs_more", "tests.test_push_sync", "tests.test_pinned", "tests.test_properties"]
SLOW = ["tests.test_features", "tests.test_backup_calendar", "tests.test_heat", "tests.test_watch"]
SWAP = {ast.Lt: ast.LtE, ast.LtE: ast.Lt, ast.Gt: ast.GtE, ast.GtE: ast.Gt, ast.Eq: ast.NotEq, ast.NotEq: ast.Eq}


def sites(tree):
    """[(kind, lineno, col, node)] of everything that can be mutated."""
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Compare) and len(n.ops) == 1 and type(n.ops[0]) in SWAP:
            out.append(("compare", n.lineno, n.col_offset, n))
        elif isinstance(n, ast.Constant) and isinstance(n.value, (int, float)) and not isinstance(n.value, bool) and n.value not in (0, 1, -1, 2, 7, 100):
            out.append(("number", n.lineno, n.col_offset, n))
    return out


def mutate(source, site):
    kind, lineno, col, _ = site
    tree = ast.parse(source)
    for n in ast.walk(tree):
        if getattr(n, "lineno", None) == lineno and getattr(n, "col_offset", None) == col:
            if kind == "compare" and isinstance(n, ast.Compare):
                n.ops = [SWAP[type(n.ops[0])]()]
                return ast.unparse(tree), f"{ast.unparse(n)}"
            if kind == "number" and isinstance(n, ast.Constant):
                old = n.value
                n.value = old * 1.1 if isinstance(old, float) else (old + max(1, round(old * 0.1)))
                return ast.unparse(tree), f"{old} -> {n.value}"
    return None, None


def run_tests(workdir, modules, timeout=180):
    env = {**os.environ, "PYTHONPATH": f"{workdir}:{workdir}/tests", "PYTHONDONTWRITEBYTECODE": "1"}
    r = subprocess.run([PY, "-W", "ignore", "-m", "unittest", "-f", *modules], cwd=workdir, env=env, capture_output=True, text=True, timeout=timeout)  # noqa: S603
    return r.returncode == 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--files", default="engine.py,insights.py,assess.py,respond.py")
    ap.add_argument("--n", type=int, default=60)
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args(argv)
    rng = random.Random(a.seed)  # noqa: S311 - a repeatable sample
    work = tempfile.mkdtemp(prefix="mutants-")
    shutil.copytree(APP, work, dirs_exist_ok=True, ignore=shutil.ignore_patterns(".venv", "__pycache__", ".git", ".coverage*"))
    pool = []
    for f in a.files.split(","):
        with open(os.path.join(APP, f), encoding="utf-8") as fh:
            src = fh.read()
        pool += [(f, s) for s in sites(ast.parse(src))]
    rng.shuffle(pool)
    if not (run_tests(work, FAST) and all(run_tests(work, [m]) for m in SLOW)):
        print("the tests do not pass on the unchanged copy; stopping")
        return 2
    killed, survived, t0 = 0, [], time.time()
    for f, site in pool[:a.n]:
        path = os.path.join(work, f)
        with open(os.path.join(APP, f), encoding="utf-8") as fh:
            original = fh.read()
        mutated, what = mutate(original, site)
        if mutated is None:
            continue
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(mutated)
        try:
            ok = run_tests(work, FAST) and all(run_tests(work, [m]) for m in SLOW)      # one process each: the suites share state
        except subprocess.TimeoutExpired:
            ok = False
        finally:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(original)
        if ok:
            survived.append((f, site[1], site[0], what))
        else:
            killed += 1
    total = killed + len(survived)
    print(f"{total} mutants in {time.time() - t0:.0f} s: {killed} killed, {len(survived)} survived ({100 * killed / max(total, 1):.0f}% killed)")
    for f, line, kind, what in sorted(survived):
        print(f"  survived: {f}:{line} {kind} {what[:90]}")
    shutil.rmtree(work, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
