"""Summarizes a results file per arm and per task, as Markdown.

    python3 eval/summarize.py [eval/results.csv]

Rows with a client and set (results-2.csv) are grouped by client, set and arm.
"""
import csv
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("results.csv")
rows = [r for r in csv.DictReader(open(src)) if r["success"] in ("0", "1")]
for r in rows:
    if r.get("client"):
        r["arm"] = f"{r['client']} {r['set']} {r['arm']}"
num = lambda r, k: float(r[k] or 0)


def line(rs):
    ok = sum(int(r["success"]) for r in rs)
    tokens = [num(r, "input_tokens") + num(r, "output_tokens") + num(r, "cache_read_tokens") + num(r, "cache_write_tokens") for r in rs]
    return (f"{ok}/{len(rs)} | {st.mean(num(r, 'tool_calls') for r in rs):.1f} | "
            f"{st.median(num(r, 'tool_calls') for r in rs):.0f} | {st.mean(tokens) / 1000:.0f}k | "
            f"{st.mean(num(r, 'output_tokens') for r in rs) / 1000:.1f}k | "
            f"{st.mean(num(r, 'wall_seconds') for r in rs):.0f} s | ${sum(num(r, 'cost_usd') for r in rs):.2f}")


by_arm, by_task = defaultdict(list), defaultdict(list)
for r in rows:
    by_arm[r["arm"]].append(r)
    by_task[(r["task"], r["arm"])].append(r)
head = "| success | calls (mean) | calls (median) | tokens, all (mean) | output tokens (mean) | wall (mean) | cost (total) |"
out = ["| arm " + head, "|---" * 8 + "|"]
out += [f"| {a} | {line(rs)} |" for a, rs in sorted(by_arm.items())]
out += ["", "| task | arm " + head, "|---" * 9 + "|"]
out += [f"| {t} | {a} | {line(rs)} |" for (t, a), rs in sorted(by_task.items())]
sys.stdout.write("\n".join(out) + "\n")
