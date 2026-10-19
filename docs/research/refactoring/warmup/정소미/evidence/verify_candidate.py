#!/usr/bin/env python3
"""Verify one candidate proof of a project-resident Lean Refactor Arena problem.

The candidate replaces lines START..END of the original source file, the whole
file (including every later declaration) is compiled with `lake env lean`, and a
second copy is compiled with `#count_heartbeats in` in front of the declaration.
Nothing inside the repository checkout is modified: generated files and logs go
to --workdir.

Checks:
  1. the candidate starts with the benchmark statement, unchanged
  2. no forbidden pattern (same regex list as the Arena upload filter)
  3. the file compiles, and `#print axioms` shows no `sorryAx`
Measurements: proof tokens (proof_tokens.py), heartbeats, wall time.

usage:
  verify_candidate.py --repo DIR --file REL.lean --start N --end M --name DECL \
      --statement statement.lean --candidate cand.lean --workdir OUT --tag TAG
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import proof_tokens  # noqa: E402

# Copied from the Arena Space (app.py, `_FORBIDDEN_PATTERNS`, snapshot 2026-10-05).
FORBIDDEN = [
    ("#eval", r"#\s*eval\b"), ("#reduce", r"#\s*reduce\b"), ("IO.", r"\bIO\."),
    ("unsafe", r"\bunsafe\s+(def|fun|theorem|lemma)\b"), ("extern", r"\bextern\b"),
    ("initialize", r"\binitialize\b"),
    ("@[implemented_by]", r"@\[\s*implemented[_]?[Bb]y\b"),
    ("@[extern]", r"@\[\s*extern\b"), ("sorry", r"\bsorry\b"),
    ("sorryAx", r"\bsorryAx\b"), ("admit", r"\badmit\b"), ("axiom", r"\baxiom\b"),
    ("native_decide", r"\bnative_decide\b"), ("ofReduceBool", r"\bofReduceBool\b"),
    ("ofReduceNat", r"\bofReduceNat\b"), ("run_cmd", r"\brun_cmd\b"),
    ("run_elab", r"\brun_elab\b"), ("#exit", r"#\s*exit\b"),
    ("#count_heartbeats", r"#\s*count_heartbeats\b"),
    ("attribute command", r"(?m)^\s*attribute\b"),
    ("macro/elab/notation", r"\b(macro|macro_rules|elab|elab_rules|notation|syntax)\b"),
    ("deriving instance", r"\bderiving\s+instance\b"),
    ("auxiliary declaration",
     r"(?m)^\s*(def|abbrev|instance|structure|inductive|class|opaque)\b"),
]
HB_RE = re.compile(r"Used (\d+) heartbeats")
IMPORT_RE = re.compile(r"^\s*((public|private|meta)\s+)*import\s")


def run_lean(repo: Path, lean_args: list[str], path: Path, timeout: int) -> dict:
    cmd = ["lake", "env", "lean", *lean_args, str(path)]
    t0 = time.monotonic()
    timed_out = False
    with subprocess.Popen(cmd, cwd=repo, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          text=True, errors="replace", start_new_session=os.name == "posix") as p:
        def kill_children():
            try:
                if os.name == "posix":
                    os.killpg(p.pid, signal.SIGKILL)
                else:
                    p.kill()
            except ProcessLookupError:
                pass

        def terminate(signum, frame):
            kill_children()
            raise SystemExit(128 + signum)

        previous = signal.signal(signal.SIGTERM, terminate)
        try:
            try:
                stdout, stderr = p.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
                kill_children()
                stdout, stderr = p.communicate()
        finally:
            signal.signal(signal.SIGTERM, previous)
        code = -1 if timed_out else p.returncode
    out = stdout + stderr + (f"\nTIMEOUT after {timeout}s\n" if timed_out else "")
    return {"command": " ".join(cmd[:-1] + [path.name]), "returncode": code,
            "seconds": round(time.monotonic() - t0, 2), "output": out,
            "timed_out": timed_out}


def parse_heartbeat(output: str, returncode: int) -> dict:
    found = HB_RE.findall(output)
    errors = [line for line in output.splitlines() if ": error" in line]
    usable = len(found) == 1 and returncode == 0 and not errors
    return {"heartbeats": int(found[0]) if usable else None,
            "measurement_ambiguous": len(found) > 1,
            "error_count": len(errors), "first_errors": errors[:3]}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", required=True, type=Path)
    ap.add_argument("--file", required=True, help="source file, relative to --repo")
    ap.add_argument("--start", required=True, type=int)
    ap.add_argument("--end", required=True, type=int)
    ap.add_argument("--name", required=True, help="fully qualified declaration name")
    ap.add_argument("--statement", required=True, type=Path)
    ap.add_argument("--candidate", required=True, type=Path)
    ap.add_argument("--workdir", required=True, type=Path)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--hb-line", type=int, default=None,
                    help="insert the heartbeat counter before this line "
                         "(default: --start; use the docstring's first line if any)")
    ap.add_argument("--extra-import", action="append", default=[],
                    help="module to import in the heartbeat copy only")
    ap.add_argument("--lean-arg", action="append", default=[])
    ap.add_argument("--timeout", type=int, default=1500)
    ap.add_argument("--skip-heartbeat", action="store_true")
    args = ap.parse_args()
    # lean runs with cwd=repo, so every generated path must be absolute
    args.repo, args.workdir = args.repo.resolve(), args.workdir.resolve()

    original = (args.repo / args.file).read_text(encoding="utf-8").split("\n")
    statement = args.statement.read_text(encoding="utf-8").rstrip("\n")
    candidate = args.candidate.read_text(encoding="utf-8").rstrip("\n")
    args.workdir.mkdir(parents=True, exist_ok=True)

    result: dict = {
        "tag": args.tag, "name": args.name, "source_file": args.file,
        "replaced_lines": [args.start, args.end],
        "candidate_sha256": hashlib.sha256(candidate.encode()).hexdigest(),
    }
    rest = candidate[len(statement):] if candidate.startswith(statement) else None
    result["statement_unchanged"] = bool(rest is not None and rest.lstrip().startswith(":="))
    stripped = proof_tokens.remove_comments(candidate)
    result["forbidden_patterns"] = [n for n, rx in FORBIDDEN if re.search(rx, stripped)]
    try:
        result["proof_tokens"] = proof_tokens.proof_length(candidate, statement)
    except ValueError as e:
        result["proof_tokens"] = None
        result["token_error"] = str(e)
    result["declaration_lines"] = len(candidate.split("\n"))

    body = original[:args.start - 1] + candidate.split("\n") + original[args.end:]
    check_path = args.workdir / f"{args.tag}.check.lean"
    check_path.write_text("\n".join(body + ["", f"#print axioms {args.name}", ""]),
                          encoding="utf-8")
    check = run_lean(args.repo, args.lean_arg, check_path, args.timeout)
    (args.workdir / f"{args.tag}.check.log").write_text(check.pop("output"), encoding="utf-8")
    log = (args.workdir / f"{args.tag}.check.log").read_text(encoding="utf-8")
    errors = [l for l in log.splitlines() if ": error" in l]
    if check["returncode"] != 0 and not errors:
        errors = [l for l in log.splitlines() if l.strip()][:5]
    axioms = [l for l in log.splitlines() if "depends on axioms" in l or "does not depend" in l]
    result["check"] = {**check, "error_count": len(errors), "first_errors": errors[:5],
                       "warning_count": sum(": warning" in l for l in log.splitlines()),
                       "axioms": axioms, "sorryAx": "sorryAx" in " ".join(axioms)}
    compiled = (check["returncode"] == 0 and not errors and bool(axioms)
                and not result["check"]["sorryAx"])
    result["compiled"] = compiled

    if not args.skip_heartbeat:
        hb_line = args.hb_line or args.start
        shift = len(candidate.split("\n")) - (args.end - args.start + 1)
        if hb_line > args.end:
            hb_line += shift
        hb_body = list(body)
        hb_body[hb_line - 1:hb_line - 1] = ["set_option Elab.async false in",
                                            "#count_heartbeats in"]
        if args.extra_import:
            last = max((i for i, l in enumerate(hb_body[:200]) if IMPORT_RE.match(l)),
                       default=-1)
            hb_body[last + 1:last + 1] = [f"import {m}" for m in args.extra_import]
        hb_path = args.workdir / f"{args.tag}.hb.lean"
        hb_path.write_text("\n".join(hb_body) + "\n", encoding="utf-8")
        hb = run_lean(args.repo, args.lean_arg, hb_path, args.timeout)
        hb_out = hb.pop("output")
        (args.workdir / f"{args.tag}.hb.log").write_text(hb_out, encoding="utf-8")
        result["heartbeat"] = {**hb, **parse_heartbeat(hb_out, hb["returncode"])}

    (args.workdir / f"{args.tag}.result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=1))
    return 0 if compiled else 1


if __name__ == "__main__":
    sys.exit(main())
