"""Run with Python: checks real process timeouts and ambiguous heartbeat output."""
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from verify_candidate import parse_heartbeat, run_lean


def assert_stopped(pid):
    for _ in range(20):
        state = subprocess.run(["ps", "-o", "stat=", "-p", pid],
                               capture_output=True, text=True).stdout.strip()
        if not state or state.startswith("Z"):
            return
        time.sleep(0.05)
    raise AssertionError(f"child {pid} is still running: {state}")


def check():
    assert parse_heartbeat("Used 42 heartbeats", 0)["heartbeats"] == 42
    for output, code in [("", 0), ("Used 42 heartbeats", 1),
                         ("x: error: failed\nUsed 42 heartbeats", 0)]:
        assert parse_heartbeat(output, code)["heartbeats"] is None
    ambiguous = parse_heartbeat("Used 1 heartbeats\nUsed 42 heartbeats", 0)
    assert ambiguous["heartbeats"] is None and ambiguous["measurement_ambiguous"]
    if os.name != "posix":
        print("Heartbeat checks passed; process-group check requires POSIX.")
        return
    with tempfile.TemporaryDirectory() as directory:
        repo = Path(directory)
        lake = repo / "lake"
        lake.write_text(f"#!{sys.executable}\n" + '''import subprocess, sys, time
if sys.argv[-1].endswith("normal.lean"):
    print("normal output")
    sys.exit(0)
subprocess.Popen([sys.executable, "-c", "import os, time; from pathlib import Path; Path('child.pid').write_text(str(os.getpid())); print('child output', flush=True); time.sleep(60)"])
print("parent output", flush=True)
print("stderr output", file=sys.stderr, flush=True)
time.sleep(60)
''')
        lake.chmod(0o755)
        previous_path = os.environ.get("PATH")
        os.environ["PATH"] = str(repo) + os.pathsep + (previous_path or "")
        try:
            normal = run_lean(repo, [], repo / "normal.lean", 3)
            assert normal["returncode"] == 0 and not normal["timed_out"]
            assert normal["output"] == "normal output\n"
            result = run_lean(repo, [], repo / "timeout.lean", 1)
            assert_stopped((repo / "child.pid").read_text())
            (repo / "child.pid").unlink()
            driver = repo / "driver.py"
            driver.write_text(
                f"import sys; sys.path.insert(0, {str(Path(__file__).resolve().parent)!r})\n"
                "from pathlib import Path\nfrom verify_candidate import run_lean\n"
                "run_lean(Path.cwd(), [], Path.cwd() / 'signal.lean', 60)\n")
            with subprocess.Popen([sys.executable, str(driver)], cwd=repo) as process:
                try:
                    for _ in range(100):
                        if (repo / "child.pid").exists():
                            break
                        time.sleep(0.02)
                    assert (repo / "child.pid").exists(), "child did not start"
                finally:
                    process.terminate()
                assert process.wait(timeout=3) == 143
            assert_stopped((repo / "child.pid").read_text())
        finally:
            if previous_path is None:
                os.environ.pop("PATH", None)
            else:
                os.environ["PATH"] = previous_path
        assert result["timed_out"] and result["returncode"] == -1
        assert all(text in result["output"] for text in
                   ["parent output", "child output", "stderr output", "TIMEOUT"])
    print("Verifier checks passed: normal output, timeout/SIGTERM child cleanup, heartbeat rejection.")


if __name__ == "__main__":
    check()
