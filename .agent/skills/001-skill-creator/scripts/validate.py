#!/usr/bin/env python3
"""
validate.py — Validate an Agent Skill directory against the agentskills.io spec.

Usage:
    python scripts/validate.py <skill-dir>
    python scripts/validate.py <skill-dir> --json     # machine-readable output
    python scripts/validate.py <skill-dir> --strict   # treat warnings as errors

Exit codes:
    0  All checks passed (errors = 0)
    1  One or more ERRORs found
    2  Usage error
"""

import sys
import os
import re
import json
import argparse
from pathlib import Path


# ── ANSI colours (suppressed when not a TTY) ─────────────────────────────────

def _colour(code: str, text: str) -> str:
    if sys.stdout.isatty():
        return f"\033[{code}m{text}\033[0m"
    return text

RED    = lambda t: _colour("31;1", t)
YELLOW = lambda t: _colour("33;1", t)
GREEN  = lambda t: _colour("32;1", t)
BOLD   = lambda t: _colour("1", t)
DIM    = lambda t: _colour("2", t)


# ── Result accumulator ────────────────────────────────────────────────────────

class Results:
    def __init__(self):
        self.errors:   list[str] = []
        self.warnings: list[str] = []
        self.infos:    list[str] = []

    def error(self, msg: str):   self.errors.append(msg)
    def warning(self, msg: str): self.warnings.append(msg)
    def info(self, msg: str):    self.infos.append(msg)

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0


# ── YAML frontmatter parser (stdlib only — no PyYAML required) ────────────────

def parse_frontmatter(text: str) -> tuple[dict, str]:
    """
    Returns (frontmatter_dict, body_text).
    Raises ValueError if frontmatter is missing or malformed.
    Only handles the simple flat/nested key: value YAML used in SKILL.md files.
    For multiline values (|, >) the raw block is preserved as a string.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("SKILL.md must start with a '---' frontmatter block.")

    # Find closing ---
    end = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end = i
            break
    if end is None:
        raise ValueError("Frontmatter block is never closed (missing closing '---').")

    fm_lines = lines[1:end]
    body = "\n".join(lines[end + 1:]).strip()

    # Parse key: value pairs (shallow; handles multiline block scalars as raw str)
    fm: dict = {}
    current_key = None
    block_indent = 0
    collecting_block = False
    block_lines: list[str] = []

    for line in fm_lines:
        if collecting_block:
            stripped = line.rstrip()
            indent = len(line) - len(line.lstrip())
            if stripped == "" or indent >= block_indent:
                block_lines.append(line[block_indent:] if stripped else "")
            else:
                fm[current_key] = "\n".join(block_lines).strip()
                collecting_block = False
                block_lines = []
                # Fall through to parse this line normally

        if not collecting_block:
            m = re.match(r'^([a-zA-Z_][\w-]*):\s*(.*)', line)
            if m:
                current_key = m.group(1)
                value = m.group(2).strip()
                if value in ("|", ">", "|2", ">2", "|-", ">-"):
                    collecting_block = True
                    block_indent = len(line) - len(line.lstrip()) + 2
                    block_lines = []
                elif value.startswith('"') and value.endswith('"'):
                    fm[current_key] = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    fm[current_key] = value[1:-1]
                else:
                    fm[current_key] = value
            elif line.startswith("  ") and current_key:
                # Continuation or nested mapping — store raw for metadata
                if current_key not in fm:
                    fm[current_key] = {}
                if isinstance(fm[current_key], dict):
                    nm = re.match(r'\s+([a-zA-Z_][\w-]*):\s*(.*)', line)
                    if nm:
                        fm[current_key][nm.group(1)] = nm.group(2).strip()

    if collecting_block:
        fm[current_key] = "\n".join(block_lines).strip()

    return fm, body


# ── Individual checks ─────────────────────────────────────────────────────────

NAME_RE = re.compile(r'^[a-z0-9]([a-z0-9-]*[a-z0-9])?$')


def check_name(fm: dict, dir_name: str, r: Results):
    if "name" not in fm or not str(fm.get("name", "")).strip():
        r.error(
            "'name' field is missing from frontmatter. "
            "(The agentskills.io open spec requires it, even though Antigravity "
            "makes it optional.)"
        )
        return

    name = str(fm["name"]).strip()

    if len(name) > 64:
        r.error(f"'name' is {len(name)} chars — max is 64.")

    if not NAME_RE.match(name):
        r.error(
            f"'name' value '{name}' is invalid. "
            "Only lowercase letters (a-z), digits (0-9), and single hyphens are "
            "allowed. Must not start or end with a hyphen, and must not contain "
            "consecutive hyphens (--)."
        )
    elif "--" in name:
        r.error(f"'name' '{name}' contains consecutive hyphens (--).")

    if name != dir_name:
        r.error(
            f"'name' field ('{name}') does not match the skill directory name "
            f"('{dir_name}'). They must be identical — case-sensitive."
        )


def check_description(fm: dict, r: Results):
    if "description" not in fm or not str(fm.get("description", "")).strip():
        r.error(
            "'description' field is missing or empty. "
            "This is the primary triggering mechanism — the agent matches user "
            "intent against this field."
        )
        return

    desc = str(fm["description"]).strip()

    if len(desc) > 1024:
        r.error(
            f"'description' is {len(desc)} chars — hard limit is 1024. "
            "Trim or move detail to the body."
        )
    elif len(desc) > 900:
        r.warning(
            f"'description' is {len(desc)} chars (limit 1024). "
            "Close to the limit — review before adding more."
        )

    if len(desc) < 30:
        r.warning(
            f"'description' is very short ({len(desc)} chars). "
            "A richer description improves triggering accuracy."
        )

    # Heuristic quality hints (warnings only)
    lower = desc.lower()
    if not any(kw in lower for kw in ("use ", "use this", "when ", "trigger")):
        r.warning(
            "Description doesn't seem to include imperative trigger phrasing "
            "(e.g. 'Use this skill when…'). "
            "Imperative descriptions improve triggering reliability."
        )


def check_compatibility(fm: dict, r: Results):
    if "compatibility" not in fm:
        return
    val = str(fm["compatibility"]).strip()
    if len(val) > 500:
        r.error(
            f"'compatibility' is {len(val)} chars — max is 500."
        )


def check_body(body: str, skill_dir: Path, r: Results):
    if not body.strip():
        r.error("SKILL.md has no body content after the frontmatter.")
        return

    lines = body.splitlines()
    if len(lines) > 500:
        r.warning(
            f"SKILL.md body is {len(lines)} lines (recommended max: 500). "
            "Move detailed reference material to references/ files for "
            "progressive disclosure."
        )

    # Check for file references and verify they exist
    # Matches: `path/to/file.ext`, [text](path), or bare paths like scripts/foo.py
    ref_patterns = [
        re.compile(r'`([a-zA-Z][^\s`]*\.[a-zA-Z]{1,10})`'),  # backtick paths
        re.compile(r'\[.*?\]\(([^)]+)\)'),                     # markdown links
        re.compile(r'(?:^|\s)(scripts/[^\s]+)', re.MULTILINE), # bare script refs
        re.compile(r'(?:^|\s)(references/[^\s]+)', re.MULTILINE),
        re.compile(r'(?:^|\s)(assets/[^\s]+)', re.MULTILINE),
    ]
    referenced: set[str] = set()
    for pat in ref_patterns:
        for m in pat.finditer(body):
            path = m.group(1).strip("`).,'\"")
            if "/" in path and not path.startswith("http") and not path.startswith("#"):
                referenced.add(path)

    for ref in sorted(referenced):
        full = skill_dir / ref
        if not full.exists():
            r.warning(
                f"Body references '{ref}' but that file doesn't exist "
                f"in the skill directory. Create it or fix the path."
            )


def check_structure(skill_dir: Path, r: Results):
    """Warn about common structural issues."""
    scripts_dir = skill_dir / "scripts"
    if scripts_dir.exists():
        for script in scripts_dir.iterdir():
            if script.is_file() and not os.access(script, os.X_OK):
                r.warning(
                    f"scripts/{script.name} is not executable. "
                    "Run: chmod +x scripts/{script.name}"
                )

    # Warn if there's a references/ dir but no reference to it in SKILL.md
    refs_dir = skill_dir / "references"
    if refs_dir.exists() and any(refs_dir.iterdir()):
        skill_md = skill_dir / "SKILL.md"
        content = skill_md.read_text()
        if "references/" not in content:
            r.warning(
                "A references/ directory exists with files but SKILL.md "
                "doesn't mention any of them. "
                "The agent won't load them unless instructed to."
            )


# ── Main validation entry point ───────────────────────────────────────────────

def validate(skill_dir: Path, strict: bool = False) -> Results:
    r = Results()

    skill_md_path = skill_dir / "SKILL.md"
    if not skill_md_path.exists():
        r.error(f"No SKILL.md found in '{skill_dir}'. A skill requires one.")
        return r

    try:
        text = skill_md_path.read_text(encoding="utf-8")
    except Exception as e:
        r.error(f"Could not read SKILL.md: {e}")
        return r

    try:
        fm, body = parse_frontmatter(text)
    except ValueError as e:
        r.error(str(e))
        return r

    dir_name = skill_dir.name
    check_name(fm, dir_name, r)
    check_description(fm, r)
    check_compatibility(fm, r)
    check_body(body, skill_dir, r)
    check_structure(skill_dir, r)

    if strict:
        r.errors.extend(r.warnings)
        r.warnings.clear()

    return r


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Validate an Agent Skill directory.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("skill_dir", help="Path to the skill directory")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument(
        "--strict", action="store_true", help="Treat warnings as errors"
    )
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir).resolve()
    if not skill_dir.exists():
        print(f"Error: '{skill_dir}' does not exist.", file=sys.stderr)
        sys.exit(2)
    if not skill_dir.is_dir():
        print(f"Error: '{skill_dir}' is not a directory.", file=sys.stderr)
        sys.exit(2)

    results = validate(skill_dir, strict=args.strict)

    if args.json:
        print(json.dumps({
            "skill_dir": str(skill_dir),
            "passed": results.ok,
            "errors": results.errors,
            "warnings": results.warnings,
            "infos": results.infos,
        }, indent=2))
        sys.exit(0 if results.ok else 1)

    # Human-readable output
    print(BOLD(f"\nValidating: {skill_dir.name}/"))
    print(DIM("─" * 50))

    if results.errors:
        for msg in results.errors:
            print(RED("  ERROR   ") + msg)
    if results.warnings:
        for msg in results.warnings:
            print(YELLOW("  WARN    ") + msg)
    if results.infos:
        for msg in results.infos:
            print(DIM("  INFO    ") + msg)

    print(DIM("─" * 50))
    if results.ok:
        print(GREEN(f"  ✓ Passed") + f"  ({len(results.warnings)} warning(s))")
    else:
        print(RED(f"  ✗ Failed") +
              f"  ({len(results.errors)} error(s), {len(results.warnings)} warning(s))")

    sys.exit(0 if results.ok else 1)


if __name__ == "__main__":
    main()
