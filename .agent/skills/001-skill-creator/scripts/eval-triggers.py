#!/usr/bin/env python3
"""
eval-triggers.py — Measure a skill description's trigger-rate accuracy.

Runs each query in an evals.json file multiple times, records whether
the skill loaded (triggered), and reports pass rates.

Usage:
    python scripts/eval-triggers.py <queries.json> [OPTIONS]

Options:
    --skill-dir DIR     Path to the skill directory to evaluate (used for
                        detection and for determining the skill name).
                        Default: current directory.
    --runs N            Number of times to run each query (default: 3).
                        More runs reduce noise; 3 is usually sufficient for
                        quick iteration.
    --threshold FLOAT   Trigger rate above which a should-trigger query is
                        considered "passing", and below which a
                        should-not-trigger query passes (default: 0.5).
    --backend NAME      Agent backend to use for running queries.
                        Options: antigravity (default), claude-code, mock.
                        See BACKENDS section below.
    --out FILE          Write JSON results to FILE in addition to stdout.
    --train-split FLOAT Fraction of queries to use as the train set when
                        reporting (default: 0.6). Validation set is the rest.
                        Shuffle is deterministic (seeded by query count).

BACKENDS:
    antigravity   Uses the Antigravity CLI. Requires the ANTIGRAVITY_CLI
                  env var to point to the antigravity executable, or 'antigravity'
                  must be on PATH. Detection checks stderr/stdout for the
                  phrase "Loading skill: <skill-name>".

    claude-code   Uses the Claude Code CLI ('claude'). Detection checks the
                  JSON output for a Skill tool_use block matching the skill name.
                  Requires 'claude' on PATH.

    mock          Simulates 60% trigger rate for all queries. For testing the
                  eval harness itself without a live agent.

Exit codes:
    0  Eval completed (not a pass/fail — check the report)
    1  Could not run evals (missing queries file, bad JSON, etc.)
    2  Usage error
"""

import sys
import os
import json
import time
import random
import argparse
import subprocess
import tempfile
from pathlib import Path
from typing import Optional


# ── Backend drivers ───────────────────────────────────────────────────────────

def _run_antigravity(query: str, skill_name: str, skill_dir: Path) -> bool:
    """
    Run a query via the Antigravity CLI and return True if the skill triggered.
    Requires ANTIGRAVITY_CLI env var or 'antigravity' on PATH.
    """
    cli = os.environ.get("ANTIGRAVITY_CLI", "antigravity")
    try:
        result = subprocess.run(
            [cli, "run", "--no-interactive", "--prompt", query,
             "--skills-dir", str(skill_dir.parent)],
            capture_output=True,
            text=True,
            timeout=120,
        )
        combined = result.stdout + result.stderr
        # Detection: Antigravity logs "Loading skill: <name>" when it activates
        return f"Loading skill: {skill_name}" in combined
    except FileNotFoundError:
        raise RuntimeError(
            f"Antigravity CLI not found. Set ANTIGRAVITY_CLI env var or ensure "
            f"'antigravity' is on PATH."
        )
    except subprocess.TimeoutExpired:
        return False


def _run_claude_code(query: str, skill_name: str, skill_dir: Path) -> bool:
    """
    Run a query via Claude Code CLI and return True if the skill triggered.
    Requires 'claude' on PATH and the skill to be installed.
    """
    try:
        result = subprocess.run(
            ["claude", "-p", query, "--output-format", "json"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            return False
        # Detection: look for Skill tool_use block with matching skill name
        messages = data.get("messages", [])
        for msg in messages:
            content = msg.get("content", [])
            if isinstance(content, list):
                for block in content:
                    if (isinstance(block, dict)
                            and block.get("type") == "tool_use"
                            and block.get("name") == "Skill"
                            and block.get("input", {}).get("skill") == skill_name):
                        return True
        return False
    except FileNotFoundError:
        raise RuntimeError("'claude' CLI not found. Ensure Claude Code is installed.")
    except subprocess.TimeoutExpired:
        return False


def _run_mock(query: str, skill_name: str, skill_dir: Path) -> bool:
    """Simulates ~60% trigger rate for testing the harness."""
    time.sleep(0.05)  # simulate latency
    return random.random() < 0.6


BACKENDS = {
    "antigravity": _run_antigravity,
    "claude-code": _run_claude_code,
    "mock": _run_mock,
}


# ── Core eval logic ───────────────────────────────────────────────────────────

def load_queries(path: Path) -> list[dict]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"Could not parse {path}: {e}")
    if not isinstance(data, list):
        raise ValueError(f"{path}: expected a JSON array at the top level.")
    for i, item in enumerate(data):
        if "query" not in item:
            raise ValueError(f"{path}: item {i} is missing a 'query' field.")
        if "should_trigger" not in item:
            raise ValueError(f"{path}: item {i} is missing a 'should_trigger' field.")
    return data


def run_eval(
    queries: list[dict],
    skill_name: str,
    skill_dir: Path,
    backend_fn,
    runs: int,
    threshold: float,
) -> list[dict]:
    results = []
    total = len(queries)
    for idx, q in enumerate(queries):
        query_text = q["query"]
        should_trigger = bool(q["should_trigger"])
        triggers = 0
        for run_i in range(runs):
            label = f"[{idx+1}/{total}] run {run_i+1}/{runs}"
            print(f"  {label}  {query_text[:60]}{'…' if len(query_text) > 60 else ''}",
                  end="\r", flush=True)
            try:
                did_trigger = backend_fn(query_text, skill_name, skill_dir)
                if did_trigger:
                    triggers += 1
            except RuntimeError as e:
                print(f"\nFatal: {e}", file=sys.stderr)
                sys.exit(1)

        trigger_rate = triggers / runs
        # A query "passes" if its trigger rate is on the correct side of threshold
        passed = (trigger_rate >= threshold) if should_trigger else (trigger_rate < threshold)

        results.append({
            "query": query_text,
            "should_trigger": should_trigger,
            "comment": q.get("comment", ""),
            "triggers": triggers,
            "runs": runs,
            "trigger_rate": round(trigger_rate, 3),
            "passed": passed,
        })
        # Clear carriage-return line
        print(" " * 80, end="\r")

    return results


def split_results(
    results: list[dict], train_frac: float
) -> tuple[list[dict], list[dict]]:
    """Deterministic train/validation split, stratified by should_trigger."""
    positives = [r for r in results if r["should_trigger"]]
    negatives = [r for r in results if not r["should_trigger"]]

    def split(lst):
        n_train = max(1, round(len(lst) * train_frac))
        # Seed with count for determinism
        rng = random.Random(len(lst))
        shuffled = lst[:]
        rng.shuffle(shuffled)
        return shuffled[:n_train], shuffled[n_train:]

    tp, vp = split(positives)
    tn, vn = split(negatives)
    return tp + tn, vp + vn


def pass_rate(subset: list[dict]) -> float:
    if not subset:
        return 0.0
    return sum(1 for r in subset if r["passed"]) / len(subset)


# ── Report rendering ──────────────────────────────────────────────────────────

def _colour(code, text):
    if sys.stdout.isatty():
        return f"\033[{code}m{text}\033[0m"
    return text

OK  = lambda t: _colour("32;1", t)
BAD = lambda t: _colour("31;1", t)
DIM = lambda t: _colour("2", t)
B   = lambda t: _colour("1", t)


def render_report(
    results: list[dict],
    train: list[dict],
    validation: list[dict],
    skill_name: str,
    runs: int,
    threshold: float,
):
    print(f"\n{B('Trigger-rate eval report')}")
    print(f"{DIM('Skill:')} {skill_name}   "
          f"{DIM('Runs per query:')} {runs}   "
          f"{DIM('Threshold:')} {threshold}")
    print(DIM("─" * 72))

    # Per-query table
    print(f"  {'PASS':<5}  {'RATE':>5}  {'EXP':>5}  QUERY")
    for r in results:
        icon = OK("  ✓  ") if r["passed"] else BAD("  ✗  ")
        exp  = "trig" if r["should_trigger"] else "skip"
        rate = f"{r['trigger_rate']:.0%}"
        q    = r["query"][:55] + ("…" if len(r["query"]) > 55 else "")
        print(f"{icon} {rate:>5}  {exp:>5}  {q}")

    print(DIM("─" * 72))

    def _pr_line(label, subset):
        if not subset:
            return
        pr = pass_rate(subset)
        bar = OK(f"{pr:.0%}") if pr >= 0.8 else (
              _colour("33;1", f"{pr:.0%}") if pr >= 0.5 else
              BAD(f"{pr:.0%}"))
        print(f"  {label:<20} {bar}  ({sum(r['passed'] for r in subset)}/{len(subset)} passed)")

    _pr_line("Overall pass rate", results)
    if validation:
        _pr_line("Train set", train)
        _pr_line("Validation set", validation)

    # Failure analysis
    failures = [r for r in results if not r["passed"]]
    if failures:
        print(f"\n{B('Failures to investigate:')}")
        for r in failures:
            direction = "under-triggered" if r["should_trigger"] else "over-triggered"
            print(f"  {BAD(direction):>18}  {r['query'][:65]}")
            print(
                f"{'':>20}  trigger rate = {r['trigger_rate']:.0%}  "
                f"(threshold = {threshold:.0%})"
            )
        print(f"\n{DIM('Tip:')} Read references/DESCRIPTION-GUIDE.md for revision strategies.")
    else:
        print(f"\n{OK('All queries passed!')} Consider writing additional near-miss eval cases.")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Measure trigger-rate accuracy for a skill description.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("queries_file", help="Path to evals/evals.json")
    parser.add_argument("--skill-dir", default=".", help="Path to the skill directory")
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument(
        "--backend",
        choices=list(BACKENDS.keys()),
        default="antigravity",
        help="Agent backend to run queries against.",
    )
    parser.add_argument("--out", help="Write JSON results to this file")
    parser.add_argument(
        "--train-split", type=float, default=0.6,
        help="Fraction of queries used as train set (default: 0.6)"
    )
    args = parser.parse_args()

    queries_path = Path(args.queries_file)
    if not queries_path.exists():
        print(f"Error: '{queries_path}' not found.", file=sys.stderr)
        sys.exit(1)

    skill_dir = Path(args.skill_dir).resolve()
    skill_name = skill_dir.name

    try:
        queries = load_queries(queries_path)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    backend_fn = BACKENDS[args.backend]

    print(f"\nRunning {len(queries)} queries × {args.runs} runs "
          f"via [{args.backend}] backend …")

    results = run_eval(queries, skill_name, skill_dir, backend_fn, args.runs, args.threshold)
    train, validation = split_results(results, args.train_split)

    render_report(results, train, validation, skill_name, args.runs, args.threshold)

    if args.out:
        out_path = Path(args.out)
        out_path.write_text(json.dumps({
            "skill": skill_name,
            "runs": args.runs,
            "threshold": args.threshold,
            "overall_pass_rate": round(pass_rate(results), 3),
            "train_pass_rate": round(pass_rate(train), 3),
            "validation_pass_rate": round(pass_rate(validation), 3),
            "results": results,
        }, indent=2), encoding="utf-8")
        print(f"\nResults written to: {args.out}")


if __name__ == "__main__":
    main()
