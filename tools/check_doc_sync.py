#!/usr/bin/env python3
"""Check that a translated Markdown document matches its source in structure.

The Korean document is the authoring source and the English document is
translated from it. Wording differs between the two, but the skeleton must
not: heading numbers, anchors, table rows and their IDs, code blocks, inline
code values and link targets. This script compares those parts and fails if
they differ.

It also reads the marker in the translated file

    <!-- translated-from: <source path> blob <git blob id> -->

and warns (without failing) when the source has changed since that blob, so
the translation is known to be behind. To see what changed:

    git diff <old blob id> <current blob id>

Usage:
    check_doc_sync.py TRANSLATED SOURCE
"""

import os
import re
import subprocess
import sys

ID_RE = re.compile(r"^(?:BC\d{2}|TC\d{2}|QA\d{2}|FR\d+-\d+|\d+(?:\.\d+)?)$")
HEADING_RE = re.compile(r"^(#{1,6})\s+(\d+(?:\.\d+)*)?")
ANCHOR_RE = re.compile(r'<a id="([^"]+)"></a>')
CODE_SPAN_RE = re.compile(r"`([^`]+)`")
LINK_RE = re.compile(r"\]\(([^)\s]+)\)")
MARKER_RE = re.compile(r"<!--\s*translated-from:\s*(\S+)\s+blob\s+([0-9a-f]{7,40})\s*-->")


def skeleton(path, counterpart):
    sk = {
        "headings": [],
        "anchors": [],
        "tables": [],
        "code blocks": [],
        "inline code": [],
        "links": [],
    }
    in_code = False
    table = None

    def close_table():
        nonlocal table
        if table is not None:
            sk["tables"].append(table)
            table = None

    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if line.startswith("```"):
            close_table()
            if not in_code:
                sk["code blocks"].append(line[3:].strip())
            in_code = not in_code
            continue
        if in_code:
            continue

        if line.startswith("|"):
            if table is None:
                table = {"rows": 0, "keys": []}
            cells = [c.strip() for c in line.strip("|").split("|")]
            if all(set(c) <= set("-: ") for c in cells):
                continue  # separator row
            table["rows"] += 1
            table["keys"] += [c for c in cells[:2] if ID_RE.match(c)]
        else:
            close_table()

        m = HEADING_RE.match(line)
        if m:
            sk["headings"].append(f"{m[1]} {m[2] or ''}".strip())
        sk["anchors"] += ANCHOR_RE.findall(line)
        sk["inline code"] += CODE_SPAN_RE.findall(line)
        for target in LINK_RE.findall(line):
            sk["links"].append("<counterpart>" if target == counterpart else target)
    close_table()

    sk["inline code"].sort()
    return sk


def first_difference(a, b):
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return i, x, y
    i = min(len(a), len(b))
    return i, (a[i] if i < len(a) else "<none>"), (b[i] if i < len(b) else "<none>")


def git_blob(path):
    try:
        out = subprocess.run(["git", "hash-object", path], check=True,
                             capture_output=True, text=True)
        return out.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def warn(msg):
    if os.environ.get("GITHUB_ACTIONS") == "true":
        print(f"::warning::{msg}")
    else:
        print(f"warning: {msg}")


def check_freshness(translated, source):
    text = open(translated, encoding="utf-8").read()
    m = MARKER_RE.search(text)
    if not m:
        warn(f"{translated}: no 'translated-from' marker; cannot tell if it is up to date")
        return
    current = git_blob(source)
    if current is None:
        warn("git is not available; skipped the up-to-date check")
        return
    if not current.startswith(m[2]):
        warn(f"{source} changed after {translated} was translated. "
             f"See: git diff {m[2]} {current[:12]}")


def main():
    if len(sys.argv) != 3:
        print(__doc__.strip().splitlines()[-1].strip(), file=sys.stderr)
        return 2
    translated, source = sys.argv[1], sys.argv[2]
    a = skeleton(translated, os.path.basename(source))
    b = skeleton(source, os.path.basename(translated))

    failed = False
    for key in a:
        if a[key] != b[key]:
            failed = True
            i, x, y = first_difference(a[key], b[key])
            print(f"[{key}] differs at #{i + 1} "
                  f"({len(a[key])} vs {len(b[key])} items)\n"
                  f"    {translated}: {x}\n"
                  f"    {source}: {y}")

    check_freshness(translated, source)

    if failed:
        print(f"FAIL: {translated} and {source} differ in structure")
        return 1
    print(f"OK: {translated} matches {source} in structure")
    return 0


if __name__ == "__main__":
    sys.exit(main())
