#!/bin/sh
# Fail if any crate in the dependency graph comes from ICU / ICU4X.
# Complements deny.toml: catches new ICU4X crate names by prefix.
set -eu
cd "$(dirname "$0")/.."

cargo metadata --format-version 1 --locked |
python3 -c '
import json, sys
banned_prefixes = ("icu", "rust_icu")
banned_names = {
    "zerovec", "zerovec-derive", "yoke", "yoke-derive", "zerofrom",
    "zerofrom-derive", "writeable", "tinystr", "litemap", "databake",
    "zerotrie", "potential_utf",
}
meta = json.load(sys.stdin)
bad = sorted({p["name"] for p in meta["packages"]
              if p["name"].startswith(banned_prefixes) or p["name"] in banned_names})
if bad:
    print("ICU-related crates found: " + ", ".join(bad))
    sys.exit(1)
print("OK: no ICU-related crates")
'
