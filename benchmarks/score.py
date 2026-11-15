#!/usr/bin/env python
"""Score an agent transcript against a rubric.

The benchmark answers one question: **does installing the skill improve the
agent's answers?** It does not run an LLM — it scores text a human or an agent
produced (see ``README.md`` for the A/B protocol).

    python benchmarks/score.py --task benchmarks/tasks/t1-config-layers.yaml \
        --transcript transcripts/baseline/t1.md
    python benchmarks/score.py --dir transcripts/baseline           # all tasks
    python benchmarks/score.py --a transcripts/baseline --b transcripts/skill \
        --markdown results/pilot.md                                 # A/B table

Rubric format (see ``tasks/*.yaml``): ``checks`` is a list of
``{name, weight, any: [regex, ...]}``; a check passes when at least one regex
matches the transcript (case-insensitive, DOTALL). ``must_not`` entries fail the
task when they match. Score = passed weight / total weight.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load_rubric(path: Path) -> dict:
    import yaml

    with path.open() as handle:
        return yaml.safe_load(handle)


def _matches(pattern: str, text: str) -> bool:
    return re.search(pattern, text, re.IGNORECASE | re.DOTALL) is not None


def score_task(rubric: dict, text: str) -> dict:
    total = 0.0
    earned = 0.0
    details = []
    for check in rubric.get("checks") or []:
        weight = float(check.get("weight", 1))
        total += weight
        passed = any(_matches(pattern, text) for pattern in check.get("any") or [])
        if passed:
            earned += weight
        details.append({"type": "check", "name": check["name"],
                        "weight": weight, "passed": passed})

    # must_not violations zero the task and are reported separately
    violations = []
    for check in rubric.get("must_not") or []:
        if _matches(check.get("pattern", ""), text):
            violations.append(check["name"])
            details.append({"type": "violation", "name": check["name"],
                            "weight": 0, "passed": False})

    score = 0.0 if violations else (earned / total if total else 0.0)
    return {
        "task": rubric.get("id") or "<unknown>",
        "title": rubric.get("title", ""),
        "score": round(score, 3),
        "earned_weight": earned,
        "total_weight": total,
        "violations": violations,
        "details": details,
    }


def score_dir(directory: Path, tasks_dir: Path) -> list[dict]:
    results = []
    for task_path in sorted(tasks_dir.glob("t*.yaml")):
        rubric = load_rubric(task_path)
        transcript = directory / f"{rubric['id']}.md"
        if not transcript.exists():
            results.append({"task": rubric["id"], "score": None,
                            "missing": str(transcript)})
            continue
        results.append(score_task(rubric, transcript.read_text()))
    return results


def summarize(results: list[dict]) -> dict:
    scored = [row for row in results if row.get("score") is not None]
    return {
        "tasks": len(scored),
        "mean_score": round(sum(row["score"] for row in scored) / len(scored), 3)
        if scored else None,
        "violations": sum(len(row.get("violations") or []) for row in scored),
        "perfect": sum(1 for row in scored if row["score"] == 1.0),
    }


def print_table(results: list[dict], title: str) -> None:
    print(f"\n== {title} ==")
    print(f"{'task':<22} {'score':>6}  {'weight':>10}  note")
    for row in results:
        if row.get("score") is None:
            print(f"{row['task']:<22} {'--':>6}  {'':>10}  missing transcript")
            continue
        note = ("VIOLATION: " + "; ".join(row["violations"])) if row["violations"] else ""
        print(f"{row['task']:<22} {row['score']:>6.3f}  "
              f"{row['earned_weight']:>4.0f}/{row['total_weight']:<4.0f}  {note}")
    summary = summarize(results)
    print(f"{'mean':<22} {summary['mean_score']:>6}  "
          f"perfect={summary['perfect']}/{summary['tasks']} "
          f"violations={summary['violations']}")


def write_markdown(a_dir: Path, b_dir: Path, tasks_dir: Path, out: Path,
                   label_a: str, label_b: str) -> None:
    a = {row["task"]: row for row in score_dir(a_dir, tasks_dir)}
    b = {row["task"]: row for row in score_dir(b_dir, tasks_dir)}
    lines = [f"# Skill A/B: {label_a} vs {label_b}", "",
             f"| task | {label_a} | {label_b} | delta |", "| --- | --- | --- | --- |"]
    for task in sorted(a):
        sa = a[task].get("score")
        sb = b[task].get("score")
        if sa is None or sb is None:
            lines.append(f"| {task} | {sa} | {sb} | -- |")
            continue
        lines.append(f"| {task} | {sa:.3f} | {sb:.3f} | {sb - sa:+.3f} |")
    sa, sb = summarize(list(a.values())), summarize(list(b.values()))
    lines += ["", "| metric | " + label_a + " | " + label_b + " |",
              "| --- | --- | --- |",
              f"| mean score | {sa['mean_score']} | {sb['mean_score']} |",
              f"| perfect tasks | {sa['perfect']}/{sa['tasks']} | {sb['perfect']}/{sb['tasks']} |",
              f"| rubric violations | {sa['violations']} | {sb['violations']} |", ""]
    out.write_text("\n".join(lines))
    print(f"wrote {out}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", type=Path, help="single rubric")
    parser.add_argument("--transcript", type=Path, help="transcript for --task")
    parser.add_argument("--dir", type=Path, help="score every task in a directory")
    parser.add_argument("--tasks-dir", type=Path, default=HERE / "tasks")
    parser.add_argument("--a", type=Path, help="baseline transcript dir")
    parser.add_argument("--b", type=Path, help="treatment transcript dir")
    parser.add_argument("--label-a", default="baseline")
    parser.add_argument("--label-b", default="skill")
    parser.add_argument("--markdown", type=Path, help="write the A/B table here")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.a and args.b:
        if args.markdown:
            write_markdown(args.a, args.b, args.tasks_dir, args.markdown,
                           args.label_a, args.label_b)
            return 0
        a = score_dir(args.a, args.tasks_dir)
        b = score_dir(args.b, args.tasks_dir)
        print_table(a, args.label_a)
        print_table(b, args.label_b)
        return 0

    if args.dir:
        results = score_dir(args.dir, args.tasks_dir)
        if args.json:
            print(json.dumps({"results": results, "summary": summarize(results)},
                             indent=2))
        else:
            print_table(results, str(args.dir))
        return 0

    if args.task and args.transcript:
        result = score_task(load_rubric(args.task), args.transcript.read_text())
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"{result['task']}: {result['score']:.3f} "
                  f"({result['earned_weight']:.0f}/{result['total_weight']:.0f})")
            for detail in result["details"]:
                mark = "ok  " if detail["passed"] else "MISS"
                print(f"  [{mark}] {detail['name']}")
        return 0

    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
