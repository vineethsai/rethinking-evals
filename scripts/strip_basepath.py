"""Strip the /rethinking-evals/ basePath prefix from the deployed site.

The Next.js export was built with basePath="/rethinking-evals", which works for
the project URL https://<user>.github.io/rethinking-evals/ but breaks under a
custom domain (manifoldoffailure.wiki) where assets are served at the apex.

This script does two passes:

  1. Replace "/rethinking-evals/" with "/" everywhere.
  2. Replace any bare "/rethinking-evals" (no trailing slash) with "" — but
     only if surrounded by a string-context delimiter ("'`<,)\\s) so we do not
     accidentally truncate strings like "vineethsai/rethinking-evals".

It runs over every tracked file with the prefix and reports remaining hits.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

BIN_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".woff", ".woff2", ".ttf", ".otf", ".pdf"}


def tracked_text_files() -> list[Path]:
    out = subprocess.check_output(["git", "ls-files", "-z"]).decode("utf-8")
    paths: list[Path] = []
    for name in out.split("\0"):
        if not name:
            continue
        p = Path(name)
        if p.suffix.lower() in BIN_EXTS:
            continue
        paths.append(p)
    return paths


def main() -> int:
    repo = Path(".").resolve()
    files = tracked_text_files()
    touched: dict[str, tuple[int, int]] = {}
    leftover_files: list[Path] = []
    # Pattern 2 enforces that a bare "/rethinking-evals" only matches at a
    # boundary that is unambiguous in our generated content: it must be either
    # immediately preceded by a quote/space/start-of-string AND immediately
    # followed by a quote, parenthesis, comma, whitespace, or end-of-string.
    pat_bare = re.compile(r'(?<=["\'`(\s,>])/rethinking-evals(?=["\'`)\s,<])')
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, FileNotFoundError):
            continue
        if "/rethinking-evals" not in text:
            continue
        before = text
        n_full = text.count("/rethinking-evals/")
        text = text.replace("/rethinking-evals/", "/")
        n_bare = len(pat_bare.findall(text))
        text = pat_bare.sub("", text)
        if text != before:
            path.write_text(text, encoding="utf-8")
            touched[str(path)] = (n_full, n_bare)
        if "/rethinking-evals" in text:
            leftover_files.append(path)
    print(f"Touched {len(touched)} files.")
    total_full = sum(v[0] for v in touched.values())
    total_bare = sum(v[1] for v in touched.values())
    print(f"  Full-prefix substitutions:   {total_full}")
    print(f"  Bare-prefix substitutions:   {total_bare}")
    if leftover_files:
        print()
        print("Files with remaining /rethinking-evals references (manual review):")
        for p in leftover_files:
            print(f"  {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
