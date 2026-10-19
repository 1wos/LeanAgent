"""Expose one configured Lean experiment through three stdio MCP tools."""

from __future__ import annotations

import argparse
import fcntl
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from harness import Experiment


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run-dir",
        type=Path,
        required=True,
        help="Directory of the configured experiment run to open.",
    )
    args = parser.parse_args()
    writer_lock = (args.run_dir / ".writer.lock").open("a")
    try:
        fcntl.flock(writer_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        parser.error("Another MCP server is already writing this run")
    experiment = Experiment.open(args.run_dir)
    mcp = FastMCP(
        "Lean experiment",
        instructions=(
            "Read get_problem before submitting candidates. Submit only a Lean tactic "
            "proof body, without the outer 'by', to evaluate_candidate. The experiment "
            "preserves the fixed original proposition and constructs the declaration. "
            "Use finish to select the verified candidate with the lowest configured "
            "metric, with the reference proof available as a fallback. No shell or "
            "general filesystem tools are available."
        ),
        log_level="ERROR",
    )

    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            openWorldHint=False,
        )
    )
    def get_problem() -> dict:
        """Return the problem context and reference proof, including original_proof_body."""
        return experiment.get_problem()

    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            openWorldHint=False,
        )
    )
    def evaluate_candidate(proof: str) -> dict:
        """Evaluate a Lean tactic proof body without the outer 'by'.

        The proof argument must contain only tactics, not a theorem declaration.
        The experiment combines the fixed original proposition with ':= by' and the
        indented body to construct the declaration. Return validation errors and the
        measured metrics supplied by the experiment; record this evaluation in the
        configured run directory.
        """
        return experiment.evaluate_candidate(proof)

    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            openWorldHint=False,
        )
    )
    def finish() -> dict:
        """Finalize the run using the verified candidate with the lowest configured metric.

        Only proofs accepted by the experiment's validation are eligible. The
        reference proof is available as a fallback, including when no new candidate
        is valid. An unverified candidate cannot be selected.
        """
        return experiment.finish()

    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
