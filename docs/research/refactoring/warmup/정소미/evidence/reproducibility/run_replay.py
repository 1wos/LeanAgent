#!/usr/bin/env python3
"""Replay the fixed P4/P9 experiment, or rebuild its tables from saved results."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE.parent
sys.path.insert(0, str(EVIDENCE))
import proof_tokens
import verify_candidate


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def git(repo, *args):
    return subprocess.check_output(["git", *args], cwd=repo, text=True).strip()


def check_environment(repo, spec):
    if git(repo, "rev-parse", "HEAD") != spec["commit"]:
        raise ValueError("project commit mismatch")
    if git(repo, "status", "--porcelain", "--untracked-files=no"):
        raise ValueError("project has tracked changes")
    if (repo / "lean-toolchain").read_text().strip() != spec["toolchain"]:
        raise ValueError("Lean toolchain mismatch")
    for name, expected in [(spec["source_file"], spec["source_sha256"]),
                           ("lake-manifest.json", spec["lake_manifest_sha256"])]:
        if digest(repo / name) != expected:
            raise ValueError(f"file hash mismatch: {name}")
    deps = []
    for dep in json.loads((repo / "lake-manifest.json").read_text())["packages"]:
        if dep.get("type") != "git":
            raise ValueError(f"unhandled dependency type: {dep['name']}")
        # Lean quotes names containing a hyphen; the directory uses the bare name.
        path = repo / ".lake/packages" / dep["name"].removeprefix("«").removesuffix("»")
        actual = git(path, "rev-parse", "HEAD")
        dirty = bool(git(path, "status", "--porcelain", "--untracked-files=no"))
        if actual != dep["rev"] or dirty:
            raise ValueError(f"dependency differs from lockfile: {dep['name']}")
        deps.append({"name": dep["name"], "commit": actual, "tracked_changes": dirty})
    lean = subprocess.check_output(["lake", "env", "lean", "--version"],
                                   cwd=repo, text=True).strip()
    return {"commit": spec["commit"], "toolchain": spec["toolchain"],
            "lean_version_output": lean, "source_sha256": spec["source_sha256"],
            "lake_manifest_sha256": spec["lake_manifest_sha256"],
            "tracked_changes": False, "dependencies": deps}


def precheck(candidate, statement):
    rest = candidate[len(statement):] if candidate.startswith(statement) else None
    if rest is None or not rest.lstrip().startswith(":="):
        return "statement_mismatch"
    stripped = proof_tokens.remove_comments(candidate)
    if any(re.search(pattern, stripped) for _, pattern in verify_candidate.FORBIDDEN):
        return "forbidden_pattern"
    return None


def run_one(repo, spec, candidate, tag, timeout, log_path, expected_axioms,
            skip_heartbeat=False):
    statement = (EVIDENCE / spec["statement"]).read_text().rstrip("\n")
    rejected = precheck(candidate.read_text().rstrip("\n"), statement)
    if rejected:
        log_path.write_text(f"Rejected before Lean execution: {rejected}\n")
        return {"tag": tag, "accepted": False, "status": rejected, "lean_invoked": False}
    with tempfile.TemporaryDirectory(prefix="leanagent-replay-") as temp:
        work = Path(temp)
        cmd = [sys.executable, str(EVIDENCE / "verify_candidate.py"),
               "--repo", str(repo), "--file", spec["source_file"],
               "--start", str(spec["start"]), "--end", str(spec["end"]),
               "--hb-line", str(spec["hb_line"]), "--name", spec["name"],
               "--statement", str(EVIDENCE / spec["statement"]),
               "--candidate", str(candidate), "--workdir", str(work),
               "--tag", tag, "--timeout", str(timeout)]
        cmd += ["--lean-arg=" + value for value in spec["lean_args"]]
        for value in spec["extra_imports"]:
            cmd += ["--extra-import", value]
        if skip_heartbeat:
            cmd += ["--skip-heartbeat"]
        try:
            process = subprocess.run(cmd, capture_output=True, text=True,
                                     timeout=2 * timeout + 30)
            stdout, stderr, returncode = process.stdout, process.stderr, process.returncode
        except subprocess.TimeoutExpired as error:
            stdout = error.stdout or b""
            stderr = error.stderr or b""
            stdout = stdout.decode(errors="replace") if isinstance(stdout, bytes) else stdout
            stderr = stderr.decode(errors="replace") if isinstance(stderr, bytes) else stderr
            returncode = -1
        logs = [f"verifier return code: {returncode}\n", stdout, stderr]
        for kind in ("check", "hb"):
            path = work / f"{tag}.{kind}.log"
            if path.exists():
                logs += [f"\n--- {kind} ---\n", path.read_text()]
        with log_path.open("a") as output:
            output.write(f"\n=== {tag} ===\n" + "\n".join(logs))
        result_path = work / f"{tag}.result.json"
        if not result_path.exists():
            return {"tag": tag, "accepted": False, "status": "execution_error",
                    "lean_invoked": True, "verifier_returncode": returncode}
        result = json.loads(result_path.read_text())
    axioms = []
    for line in result["check"]["axioms"]:
        match = re.search(r"\[([^]]*)\]", line)
        if match:
            axioms.extend(x.strip() for x in match[1].split(",") if x.strip())
    result["axioms_match"] = sorted(axioms) == sorted(expected_axioms)
    heartbeat_ok = (result.get("heartbeat", {}).get("returncode") == 0
                    and result.get("heartbeat", {}).get("heartbeats") is not None)
    accepted = (returncode == 0 and result["compiled"] and result["statement_unchanged"]
                and not result["forbidden_patterns"] and result["axioms_match"]
                and (heartbeat_ok or skip_heartbeat))
    result.update(accepted=accepted, lean_invoked=True, verifier_returncode=returncode,
                  status="accepted" if accepted else "verification_failed")
    return result


def summarize(output):
    records = json.loads((output / "results.json").read_text())
    protocol = json.loads((output / "protocol.json").read_text())
    rows = []
    for env, spec in protocol["environments"].items():
        for candidate in ("reference", "final"):
            runs = [r for r in records if r["environment"] == env and r["candidate"] == candidate]
            good = [r for r in runs if r["accepted"]]
            lengths = [r["proof_tokens"] for r in good]
            hbs = [r["heartbeat"]["heartbeats"] for r in good]
            seconds = [r["check"]["seconds"] for r in good]
            rows.append({"environment": env, "problem": spec["problem"],
                         "candidate": candidate, "runs": len(runs), "accepted": len(good),
                         "proof_tokens": lengths[0] if lengths and len(set(lengths)) == 1 else None,
                         "heartbeat": hbs[0] if hbs and len(set(hbs)) == 1 else None,
                         "stable": len(good) == protocol["repetitions"]
                                   and len(set(lengths)) == len(set(hbs)) == 1,
                         "check_seconds_min": min(seconds) if seconds else None,
                         "check_seconds_max": max(seconds) if seconds else None})
    with (output / "summary.csv").open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    save(output / "summary.json", rows)
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repos", type=Path, help="JSON mapping environment IDs to checkouts")
    parser.add_argument("--output", type=Path, help="New, empty result directory")
    parser.add_argument("--summarize", type=Path, help="Rebuild tables from saved results only")
    args = parser.parse_args()
    if args.summarize:
        summarize(args.summarize)
        return 0
    if not args.repos or not args.output:
        parser.error("provide --repos and --output, or --summarize")
    output = args.output.resolve()
    if output.exists() and any(output.iterdir()):
        parser.error("output directory must be empty")
    output.mkdir(parents=True, exist_ok=True)
    (output / "logs").mkdir()
    protocol = json.loads((HERE / "protocol.json").read_text())
    repos = {key: Path(value).expanduser().resolve()
             for key, value in json.loads(args.repos.read_text()).items()}
    save(output / "protocol.json", protocol)
    manifest = {"started_utc": datetime.now(timezone.utc).isoformat(),
                "system": platform.system(), "system_release": platform.release(),
                "machine": platform.machine(), "python": platform.python_version(),
                "protocol_sha256": digest(HERE / "protocol.json"),
                "scripts_sha256": {p.name: digest(p) for p in
                                   (Path(__file__), EVIDENCE / "verify_candidate.py",
                                    EVIDENCE / "proof_tokens.py")}, "environments": {}}
    for env, spec in protocol["environments"].items():
        manifest["environments"][env] = check_environment(repos[env], spec)
        if digest(EVIDENCE / spec["statement"]) != spec["statement_sha256"]:
            raise ValueError("statement input hash mismatch")
        for candidate in spec["candidates"].values():
            if digest(EVIDENCE / candidate["path"]) != candidate["sha256"]:
                raise ValueError("candidate input hash mismatch")
        statement = (EVIDENCE / spec["statement"]).read_text().rstrip("\n")
        reference = (EVIDENCE / spec["candidates"]["reference"]["path"]).read_text()
        if proof_tokens.proof_length(reference, statement) != spec["reference_proof_length"]:
            raise ValueError("reference proof length mismatch")
    save(output / "environment.json", manifest)
    records = []
    for env, spec in protocol["environments"].items():
        for repeat in range(1, protocol["repetitions"] + 1):
            for name, candidate in spec["candidates"].items():
                tag = f"{env}-{name}-{repeat}"
                result = run_one(repos[env], spec, EVIDENCE / candidate["path"], tag,
                                 protocol["timeout_seconds"], output / "logs" / f"{env}-{name}.log",
                                 protocol["expected_axioms"])
                result.update(environment=env, candidate=name, repeat=repeat,
                              candidate_file_sha256=candidate["sha256"])
                records.append(result)
                save(output / "results.json", records)
                print(f"{tag}: {result['status']}", flush=True)
    # Deliberately bad inputs exercise failure recording; they are never candidates.
    env = "p9-4.32"
    spec = protocol["environments"][env]
    statement = (EVIDENCE / spec["statement"]).read_text().rstrip("\n")
    controls = []
    fixtures = {
        "changed-statement": (statement.replace("choice q r", "choice p r") + " := by trivial", "statement_mismatch"),
        "forbidden-proof": (statement + " := by sorry", "forbidden_pattern"),
        "compiler-error": (statement + " := by exact noSuchLemmaForReplayControl", "verification_failed"),
    }
    with tempfile.TemporaryDirectory(prefix="leanagent-controls-") as temp:
        for name, (text, expected) in fixtures.items():
            candidate = Path(temp) / f"{name}.lean"
            candidate.write_text(text + "\n")
            result = run_one(repos[env], spec, candidate, name, protocol["timeout_seconds"],
                             output / "logs" / f"control-{name}.log",
                             protocol["expected_axioms"], skip_heartbeat=True)
            result.update(expected_status=expected,
                          matched_expectation=result["status"] == expected and not result["accepted"])
            controls.append(result)
    try:
        check_environment(repos["p9-4.31"], spec)
        error = None
    except ValueError as exception:
        error = str(exception)
    controls.append({"tag": "wrong-environment", "lean_invoked": False,
                     "accepted": False, "observed_error": error,
                     "matched_expectation": error == "project commit mismatch"})
    save(output / "controls.json", controls)
    rows = summarize(output)
    manifest["finished_utc"] = datetime.now(timezone.utc).isoformat()
    save(output / "environment.json", manifest)
    passed = all(row["stable"] for row in rows) and all(c["matched_expectation"] for c in controls)
    print(f"{len(records)} measured runs; {len(controls)} controls; protocol checks passed={passed}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
