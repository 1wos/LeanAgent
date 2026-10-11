#!/usr/bin/env python3
"""Print a Markdown table of every verified attempt, read straight from the
`*.result.json` files that verify_candidate.py wrote (not from any summary).

usage: attempt_table.py <runs-dir> <baseline-tokens> <baseline-heartbeats> [prefix]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def pct(base: int, new: int | None) -> str:
    return "-" if new is None else f"{(base - new) / base * 100:.2f}%"


def main() -> int:
    runs, base_tok, base_hb = Path(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
    prefix = sys.argv[4] if len(sys.argv) > 4 else "attempt_"
    print("| 시도 | 컴파일 | 증명 토큰 | 토큰 감소율 | heartbeat | heartbeat 감소율 | 두 감소율의 평균 |")
    print("| --- | --- | ---: | ---: | ---: | ---: | ---: |")
    for path in sorted(runs.glob(f"{prefix}*.result.json")):
        r = json.loads(path.read_text(encoding="utf-8"))
        ok = r["compiled"] and r["statement_unchanged"] and not r["forbidden_patterns"]
        tok = r.get("proof_tokens")
        hb = (r.get("heartbeat") or {}).get("heartbeats") if ok else None
        if ok and tok is not None and hb is not None:
            mean = f"{((base_tok - tok) / base_tok + (base_hb - hb) / base_hb) * 50:.2f}%"
        else:
            mean = "-"
        print(f"| `{r['tag']}` | {'통과' if ok else '실패'} | {tok if tok is not None else '-'} | "
              f"{pct(base_tok, tok) if ok else '-'} | {hb if hb is not None else '-'} | "
              f"{pct(base_hb, hb)} | {mean} |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
