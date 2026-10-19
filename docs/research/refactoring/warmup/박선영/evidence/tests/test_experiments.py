"""Pure-Python regression tests; never invoke Lake or an external checkout."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "run_experiments.py"
spec = importlib.util.spec_from_file_location("experiments", SCRIPT)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class CandidateTests(unittest.TestCase):
    statement = "theorem demo : True"

    def test_unchanged_statement(self):
        self.assertEqual(runner.validate_candidate(self.statement + " := by\n  trivial", self.statement), [])

    def test_changed_statement(self):
        with self.assertRaises(ValueError):
            runner.validate_candidate("theorem demo : False := by\n  trivial", self.statement)

    def test_term_proof_rejected(self):
        with self.assertRaises(ValueError):
            runner.validate_candidate(self.statement + " := True.intro", self.statement)

    def test_top_level_command_rejected(self):
        with self.assertRaises(ValueError):
            runner.validate_candidate(self.statement + " := by\n  trivial\n#print axioms demo", self.statement)

    def test_forbidden_patterns(self):
        for body in ("sorry", "admit", "native_decide", "run_tac skip", "axiom bad : False",
                     "lemma bad : False := by sorry"):
            with self.subTest(body=body):
                self.assertTrue(runner.validate_candidate(self.statement + " := by\n  " + body, self.statement))

    def test_comments_not_executable(self):
        self.assertEqual(runner.validate_candidate(self.statement + " := by\n  -- sorry\n  trivial", self.statement), [])

    def test_splice_once(self):
        self.assertEqual(runner.splice("prefix original suffix", "original", "candidate"), "prefix candidate suffix")

    def test_splice_missing_duplicate_empty(self):
        for source, original in (("other", "original"), ("xx", "x"), ("text", "")):
            with self.subTest(source=source, original=original), self.assertRaises(ValueError):
                runner.splice(source, original, "new")

    def test_all_official_token_counts(self):
        rows = runner.rows()
        self.assertEqual(len(rows), 15)
        for row in rows:
            with self.subTest(name=row["name"]):
                self.assertEqual(runner.tokens.proof_length(row["src"], row["statement"]), row["proof_length"])

    def test_real_drafts_only_intended_change(self):
        for number in (8, 11):
            folder = runner.HERE / f"P{number}"
            original = (folder / "reference.lean").read_text().rstrip("\n")
            draft = (folder / "attempts/attempt_01.lean").read_text().rstrip("\n")
            self.assertEqual(runner.validate_candidate(draft, runner.problem(number)["statement"]), [])
            self.assertNotEqual(original, draft)
            if number == 8:
                self.assertEqual(draft, original.replace(
                    "      apply ParallelReduction.par <;>\n        apply ParallelReduction.par <;>\n        grind",
                    "      exact .par (.par h.1 hb') (.par h.2.1 hb')"))
            else:
                start = original.index("  -- Set up the even and odd refinement polynomials\n")
                end = original.index("  set P₀ := evenRefinement", start)
                self.assertEqual(draft, original[:start] + original[end:])
                self.assertEqual(original.count("P₀_coeffs"), 1)
                self.assertEqual(original.count("P₁_coeffs"), 1)


class MeasurementTests(unittest.TestCase):
    def test_axiom_parse(self):
        log = "'Ns.demo' depends on axioms: [propext, Classical.choice, Quot.sound]\n"
        self.assertEqual(runner.axioms(log, "Ns.demo"), sorted(runner.ALLOWED_AXIOMS))

    def test_axiom_free_proof(self):
        line = "'Ns.demo' does not depend on any axioms\n"
        self.assertEqual(runner.axioms(line, "Ns.demo"), [])
        self.assertTrue(runner.valid_check({"exit_code": 0}, line, []))
        self.assertTrue(runner.valid_check({"exit_code": 0}, "", ["propext"]))
        self.assertIsNone(runner.axioms(line * 2, "Ns.demo"))
        self.assertIsNone(runner.axioms(line, "other"))
        self.assertIsNone(runner.axioms(line + "'Ns.demo' depends on axioms: []\n", "Ns.demo"))

    def test_axiom_missing_duplicate_wrong_name(self):
        line = "'demo' depends on axioms: [sorryAx]\n"
        for log, name in (("", "demo"), (line * 2, "demo"), (line, "other")):
            self.assertIsNone(runner.axioms(log, name))

    def test_valid_check_rejects_error_exit_and_axioms(self):
        standard = sorted(runner.ALLOWED_AXIOMS)
        self.assertTrue(runner.valid_check({"exit_code": 0}, "", standard))
        for exit_code, log, dependencies in ((1, "", standard), (None, "", standard),
                (0, "file:1:1: error: failure", standard), (0, "", None),
                (0, "", ["sorryAx"]), (0, "", standard + ["sorryAx"]), (0, "", ["Unknown.axiom"])):
            with self.subTest(dependencies=dependencies, exit_code=exit_code):
                self.assertFalse(runner.valid_check({"exit_code": exit_code}, log, dependencies))

    def test_heartbeat_parse(self):
        self.assertEqual(runner.measured_heartbeat({"exit_code": 0, "stdout": "Used 123 heartbeats", "stderr": ""}), 123)

    def test_heartbeat_rejects_missing_multiple_failure(self):
        for code, output in ((0, ""), (1, "Used 123 heartbeats"), (None, "Used 123 heartbeats"),
                             (0, "Used 1 heartbeats\nUsed 2 heartbeats"),
                             (0, "Used 1 heartbeats\nf:1: error: failed")):
            self.assertIsNone(runner.measured_heartbeat({"exit_code": code, "stdout": output, "stderr": ""}))

    def test_instrument_before_doc_comment(self):
        candidate = "theorem demo : True := by\n  trivial"
        source = "module\npublic import A\n/-- Doc. -/\n" + candidate
        measured = runner.heartbeat_source(source, candidate)
        self.assertIn("public import A\nimport Mathlib.Util.CountHeartbeats", measured)
        self.assertIn("set_option Elab.async false in\n#count_heartbeats in\n/-- Doc. -/\n" + candidate, measured)

    def test_instrument_before_omit(self):
        candidate = "theorem demo : True := by\n  trivial"
        measured = runner.heartbeat_source("import A\nomit x in\n" + candidate, candidate)
        self.assertIn("#count_heartbeats in\nomit x in\n" + candidate, measured)

    def test_no_import_fails(self):
        with self.assertRaises(ValueError):
            runner.heartbeat_source("theorem demo : True := by trivial", "theorem demo")

    def test_timeout_normalizes_bytes(self):
        timeout = subprocess.TimeoutExpired(["lean"], 1, output=b"partial", stderr=b"failure")
        with patch.object(runner.subprocess, "run", side_effect=timeout):
            result = runner.command(["lean"], runner.ROOT, 1)
        self.assertEqual(result["status"], "timeout")
        self.assertIsNone(result["exit_code"])
        self.assertEqual(result["stdout"], "partial")
        self.assertEqual(result["stderr"], "failure")

    def test_reduction(self):
        self.assertEqual(runner.reduction(100, 80), 20)
        self.assertEqual(runner.reduction(100, 120), -20)
        for a, b in ((None, 1), (1, None), (0, 1)):
            self.assertIsNone(runner.reduction(a, b))


class ReportTests(unittest.TestCase):
    def test_output_is_author_local(self):
        self.assertEqual(runner.OUTPUT, runner.HERE / "metrics")

    def test_legacy_output_path_resolves_to_relocated_evidence(self):
        self.assertEqual(runner.recorded_output_path("metrics/warmup/박선영/P11/runs/example"),
                         runner.OUTPUT / "P11/runs/example")

    def test_current_output_path_is_not_relocated_again(self):
        path = runner.OUTPUT / "P8/runs/example"
        self.assertEqual(runner.recorded_output_path(runner.relative(path)), path)

    def test_rendering_preserves_historical_records(self):
        data = json.loads((runner.OUTPUT / "metrics.json").read_text())
        before = json.dumps(data, ensure_ascii=False, sort_keys=True)
        table = runner.render_table(data)
        self.assertIn('href="evidence/metrics/', table)
        self.assertNotIn("../../../../../metrics/", table)
        self.assertEqual(json.dumps(data, ensure_ascii=False, sort_keys=True), before)

    def test_all_versions_and_no_false_success(self):
        data = runner.aggregate()
        self.assertEqual([p["compatibility"]["required"] for p in data["problems"]], [4, 3])
        for item in data["problems"]:
            for pair in item["versions"]:
                reference, candidate = pair["reference"], pair["candidate"]
                passed = reference and candidate and reference["status"] == candidate["status"] == "passed"
                for key in ("token", "heartbeat"):
                    self.assertEqual(pair[f"{key}_reduction_pct"] is not None, bool(passed))
        table = runner.render_table(data)
        for item in data["problems"]:
            for pair in item["versions"]:
                self.assertIn(pair["version"], table)
        self.assertIn("tokens", table)
        missing = {"problems": [{"problem": 8, "draft_candidates": [],
            "compatibility": {"passed": 0, "required": 4, "tested": 0},
            "versions": [{"version": "v4.31.0", "reference": None, "candidate": None,
                "token_reduction_pct": None, "heartbeat_reduction_pct": None}]}]}
        self.assertNotIn("% 감소", runner.render_table(missing))

    def test_html_escape_and_existing_evidence_link(self):
        data = runner.aggregate()
        data["problems"][0]["versions"][0]["version"] = '<script>&"'
        table = runner.render_table(data)
        self.assertIn("&lt;script&gt;&amp;&quot;", table)
        self.assertNotIn("<script>", table)
        import html
        import re
        for link in re.findall(r'href="([^"]+)"', table):
            self.assertTrue((runner.HERE.parent / html.unescape(link)).exists(), link)

    def test_aggregate_hashes_and_axioms_match_saved_files(self):
        for item in runner.aggregate()["problems"]:
            if item["selected"]:
                selected = (runner.ROOT / item["selected"]).read_text().rstrip("\n")
                self.assertEqual(runner.digest(selected), item["selected_sha256"])
                self.assertTrue(any(run["candidate_sha256"] == item["selected_sha256"] and run["valid"]
                                    for run in item["attempts"]))
            for pair in item["versions"]:
                if pair["candidate"] and pair["candidate"]["valid"] and pair["reference"]:
                    self.assertLessEqual(set(pair["candidate"]["axioms"]), set(pair["reference"]["axioms"]))
            for run in item["attempts"]:
                path = runner.ROOT / run["candidate"]
                self.assertEqual(runner.digest(path.read_text().rstrip("\n")), run["candidate_sha256"])
                if run["valid"]:
                    self.assertLessEqual(set(run["axioms"]), runner.ALLOWED_AXIOMS)
                self.assertTrue((runner.recorded_output_path(run["output"]) / "check.log").exists())
                if "measurement" in run:
                    self.assertTrue((runner.recorded_output_path(run["output"]) / "heartbeat.log").exists())

    def test_summary_updates_only_marker_section(self):
        data = runner.aggregate()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            here = root / "evidence"
            here.mkdir()
            page = root / "presentation.html"
            begin, end = runner.MARKERS
            page.write_text("before" + begin + "old" + end + "after")
            with patch.object(runner, "HERE", here), patch.object(runner, "OUTPUT", root / "metrics"), \
                    patch.object(runner, "aggregate", return_value=data), \
                    patch.object(runner, "relative", return_value="metrics/metrics.json"):
                expected = runner.render_table(data)
                runner.summarize(True)
            content = page.read_text()
            self.assertTrue(content.startswith("before" + begin))
            self.assertTrue(content.endswith(end + "after"))
            self.assertIn(expected, content)


if __name__ == "__main__":
    unittest.main()
