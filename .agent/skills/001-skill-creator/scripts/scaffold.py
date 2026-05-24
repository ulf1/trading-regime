#!/usr/bin/env python3
"""
scaffold.py -- Scaffold a new Agent Skill directory.

Usage:
    python scripts/scaffold.py <name>
    python scripts/scaffold.py <name> --desc "What this skill does"
    python scripts/scaffold.py <name> --dest ~/.gemini/antigravity/skills/
    python scripts/scaffold.py <name> --full
    python scripts/scaffold.py --suggest "My PDF Extractor 2.0"

Exit codes:
    0  Success
    1  Validation error
    2  Destination already exists
"""

import sys
import os
import re
import argparse
from pathlib import Path

NAME_RE = re.compile(r'^[a-z0-9]([a-z0-9-]*[a-z0-9])?$')


# --------------------------------------------------------------------------- #
# Templates                                                                    #
# --------------------------------------------------------------------------- #

def skill_md_template(name: str, title: str, description: str) -> str:
    return f"""\
---
name: {name}
description: >
  {description}
---

# {title}

<!-- One sentence: what does this skill achieve? -->

## Instructions

<!-- Step-by-step procedure. Be prescriptive where the task is fragile;
     give the agent freedom where multiple approaches are equally valid. -->

1. Step one.
2. Step two.
3. Step three.

## Output format

<!-- Provide a concrete template. Pattern-matching against examples is
     more reliable than prose descriptions of what to produce.
     Delete this section if output is unconstrained. -->

```
<!-- your output template here -->
```

## Gotchas

<!-- Concrete, environment-specific surprises the agent would otherwise
     get wrong. Not general advice -- specific corrections.
     Delete this section if there are no known gotchas. -->

- _None yet. Add as you discover them._

## Constraints

<!-- Hard "do not" rules. Delete if not needed. -->

- _None yet._
"""


def script_stub_template(name: str) -> str:
    lines = [
        "#!/usr/bin/env python3",
        f'"""Helper script for the {name} skill.',
        "",
        "Usage:",
        "    python scripts/run.py [OPTIONS] <input>",
        "",
        "Options:",
        '    --help    Show this help message and exit',
        '"""',
        "# TODO: implement",
        "import sys",
        "import argparse",
        "",
        "",
        "def main():",
        "    parser = argparse.ArgumentParser(description=__doc__)",
        '    parser.add_argument("input", help="Input to process")',
        "    args = parser.parse_args()",
        '    print(f"Processing: {args.input}")',
        "",
        "",
        'if __name__ == "__main__":',
        "    main()",
        "",
    ]
    return "\n".join(lines)


def reference_stub_template(title: str) -> str:
    return f"""\
# Reference -- {title}

<!-- Detailed technical reference, API docs, lookup tables, checklists.
     Keep this file focused: agents load it on demand, so smaller files
     mean less context used when the reference isn't needed.

     Reference from SKILL.md:
       Read `references/REFERENCE.md` when you need details about X.
-->

## Overview

_Describe what this reference covers._
"""


def evals_stub_template() -> str:
    return """\
[
  {
    "comment": "Should trigger -- direct domain mention",
    "query": "TODO: write a prompt that should activate this skill",
    "should_trigger": true
  },
  {
    "comment": "Should trigger -- oblique/indirect phrasing",
    "query": "TODO: same intent, different words",
    "should_trigger": true
  },
  {
    "comment": "Should NOT trigger -- near-miss (shares keywords but needs something else)",
    "query": "TODO: a prompt that looks similar but needs a different skill",
    "should_trigger": false
  },
  {
    "comment": "Should NOT trigger -- clearly unrelated",
    "query": "TODO: unrelated prompt",
    "should_trigger": false
  }
]
"""


# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #

def slugify(name: str) -> str:
    s = name.lower().strip()
    s = re.sub(r'[^a-z0-9]+', '-', s)
    s = s.strip('-')
    s = re.sub(r'-{2,}', '-', s)
    return s


def titlify(name: str) -> str:
    return " ".join(w.capitalize() for w in name.replace("-", " ").split())


def validate_name(name: str):
    """Return error message string if invalid, else None."""
    if not name:
        return "Name cannot be empty."
    if len(name) > 64:
        return f"Name is {len(name)} chars -- max is 64."
    if not NAME_RE.match(name):
        return (
            f"'{name}' is not a valid skill name. "
            "Use only lowercase letters (a-z), digits (0-9), and single hyphens. "
            "Must not start or end with a hyphen or contain consecutive hyphens."
        )
    return None


def mkfile(path: Path, content: str, dry_run: bool):
    if dry_run:
        print(f"  [dry-run] would create: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"  created:  {path}")


# --------------------------------------------------------------------------- #
# Main scaffold logic                                                           #
# --------------------------------------------------------------------------- #

def scaffold(name: str, description: str, dest: Path, full: bool, dry_run: bool) -> Path:
    skill_dir = dest / name
    title = titlify(name)

    mkfile(skill_dir / "SKILL.md",
           skill_md_template(name, title, description), dry_run)

    if full:
        mkfile(skill_dir / "scripts" / "run.py",
               script_stub_template(name), dry_run)
        mkfile(skill_dir / "references" / "REFERENCE.md",
               reference_stub_template(title), dry_run)
        mkfile(skill_dir / "evals" / "evals.json",
               evals_stub_template(), dry_run)
        if not dry_run:
            sp = skill_dir / "scripts" / "run.py"
            if sp.exists():
                sp.chmod(sp.stat().st_mode | 0o111)

    return skill_dir


# --------------------------------------------------------------------------- #
# CLI                                                                          #
# --------------------------------------------------------------------------- #

def main():
    parser = argparse.ArgumentParser(
        description="Scaffold a new Agent Skill directory.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "name", nargs="?",
        help="Skill name (lowercase with hyphens, e.g. 'pdf-extractor').",
    )
    parser.add_argument(
        "--desc",
        default=(
            "TODO: Describe what this skill does and when to trigger it. "
            "Use imperative phrasing: 'Use this skill when the user asks to...'"
        ),
        help="Initial description for the SKILL.md frontmatter.",
    )
    parser.add_argument(
        "--dest", default=".agent/skills",
        help="Parent directory to create the skill in (default: .agent/skills).",
    )
    parser.add_argument(
        "--full", action="store_true",
        help="Also create scripts/run.py, references/REFERENCE.md, and evals/evals.json stubs.",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print what would be created without writing any files.",
    )
    parser.add_argument(
        "--suggest", metavar="HUMAN_NAME",
        help="Suggest a valid skill name from a human-readable string, then exit.",
    )
    args = parser.parse_args()

    if args.suggest:
        suggested = slugify(args.suggest)
        err = validate_name(suggested)
        if err:
            print(f"Could not derive a valid name: {err}", file=sys.stderr)
            sys.exit(1)
        print(f"Suggested name: {suggested}")
        sys.exit(0)

    if not args.name:
        parser.error("'name' argument is required (or use --suggest).")

    name = args.name
    converted = slugify(name)
    if converted != name:
        print(f"Note: '{name}' normalised to '{converted}'.", file=sys.stderr)
        name = converted

    err = validate_name(name)
    if err:
        print(f"Error: {err}", file=sys.stderr)
        sys.exit(1)

    dest = Path(args.dest)
    skill_dir = dest / name

    if skill_dir.exists() and not args.dry_run:
        print(f"Error: '{skill_dir}' already exists. Delete it or choose a different name.",
              file=sys.stderr)
        sys.exit(2)

    mode = " (--full)" if args.full else ""
    print(f"\nScaffolding skill '{name}' in {dest}/{mode}")

    skill_path = scaffold(name, args.desc, dest, args.full, args.dry_run)

    if not args.dry_run:
        print(f"\nNext steps:")
        print(f"  1. Edit     {skill_path}/SKILL.md")
        print(f"  2. Validate  python skill-creator/scripts/validate.py {skill_path}")
        print(f"  3. Restart Antigravity (Cmd/Ctrl+Shift+P -> 'Restart Agent')")


if __name__ == "__main__":
    main()
