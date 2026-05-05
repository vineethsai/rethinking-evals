"""Apply paper-faithful copy edits to the manifold-of-failure homepage.

Two encodings exist for the same text strings on the homepage:
  - Rendered DOM in index.html: HTML entities (&quot; for ").
  - RSC payload in __next.__PAGE__.txt / index.txt / __next._full.txt: JSON
    string with single-backslash escapes (\").
  - Embedded <script> RSC payload in index.html: JSON-inside-JS string with
    triple-backslash escapes (\\\").

We do exact-string replacement for each variant. Run from the repo root.
"""
from __future__ import annotations

import sys
from pathlib import Path

# (label, old, new)
# Old/new are written in the *rendered* form. We then auto-derive both the
# JSON-escape form and the JS-in-script form for substitution.
EDITS: list[tuple[str, str, str]] = [
    (
        "why-text1",
        "Standard automated red-teaming (like PAIR or TAP) acts like a heat-seeking missile: it finds a single severe failure and stops.",
        "Optimization-based red-teaming (GCG, PAIR, TAP) hill-climbs toward one worst-case failure. It tells you whether a model can be broken, but not the shape of how it breaks.",
    ),
    (
        "why-text2",
        ' (Multi-dimensional Archive of Phenotypic Elites) acts like a floodlight. It maintains an "archive" or grid representing different behavioral strategies. Instead of just finding *one* way to jailbreak a model, it finds *all* the ways.',
        " is an illumination algorithm, not an optimization one. It maintains a 25\u00d725 archive over a behavioral space (query indirection \u00d7 authority framing) and tries to fill every cell with the most-misaligned prompt it can find. The result is a global map of the failure manifold: up to 370 distinct vulnerability niches per model and up to 63% behavioral coverage on a 15,000-evaluation budget.",
    ),
    (
        "ad-text1",
        'We measure failure not just as a binary "jailbreak/no-jailbreak", but on a continuous spectrum.',
        "Failure is a spectrum, not a binary.",
    ),
    (
        "ad-text2",
        " measures how far a model strays from its safety alignment. A score of 0.0 means the model successfully refused the harmful request. A score of 1.0 indicates a catastrophic safety failure where the model fully complied with the adversarial instructions.",
        " is the worst-case judge score across ten harm categories \u2014 violence, hate speech, sexual content, self-harm, illegal activity, privacy violation, misinformation, malware, fraud, and regulated advice. Two LLM judges (GPT-4.1 and Claude Sonnet 4.5) score each response in [0, 1], and AD is the maximum across categories. 0.0 is a clean refusal; 1.0 is full compliance with a harmful request.",
    ),
    (
        "card-explorer",
        "Interact with the final MAP-Elites archives, including a live 3D safety landscape and evolution timeline.",
        "Browse the per-model 25\u00d725 archives \u2014 heatmaps, contour plots, 3D surfaces of Alignment Deviation, and a live timeline of the 15,000-iteration search.",
    ),
    (
        "card-leaderboard",
        "Compare models on Coverage, Diversity, and QD-Score. Click any datapoint to drill into that model.",
        "Compare Llama-3-8B, GPT-OSS-20B, and GPT-5-Mini on coverage, diversity (cells with AD > 0.5), peak/mean AD, and QD-Score.",
    ),
    (
        "card-correlations",
        "Cross-model heatmaps, consensus failure zones, parallel coordinates, and attack vocabulary mining.",
        "Cross-model heatmaps, consensus basins, parallel coordinates over the (a1, a2) behavioral space, and attack-vocabulary mining.",
    ),
    (
        "card-deepdives",
        "See how MAP-Elites drastically outperforms standard baselines like GCG, PAIR, and TAP.",
        "MAP-Elites vs GCG, PAIR, TAP and Random on a 15,000-query budget \u2014 plus three continuous defenses (perplexity filter, paraphrase wrapper, constitutional rewriter) that contract Llama-3-8B's basins but never erase them.",
    ),
    (
        "meta-description",
        "Mapping the manifold of LLM safety failures",
        "Quality-Diversity (MAP-Elites) red-teaming on Llama-3-8B, GPT-OSS-20B, and GPT-5-Mini. 25\u00d725 behavioral grid, Alignment Deviation across ten harm categories, basin persistence under continuous defenses.",
    ),
]


def html_form(s: str) -> str:
    return s.replace('"', "&quot;")


def json_form(s: str) -> str:
    # Single-backslash JSON-escape (matches *.txt RSC payloads).
    return s.replace("\\", "\\\\").replace('"', '\\"')


def script_form(s: str) -> str:
    # JSON inside JS string literal in <script>: each backslash and each quote
    # of the JSON-encoded form becomes `\\` and `\"`.
    j = json_form(s)
    return j.replace("\\", "\\\\").replace('"', '\\"')


def replace_all_forms(text: str, old: str, new: str, label: str) -> tuple[str, dict]:
    counts: dict[str, int] = {}
    for form_name, fn in (("html", html_form), ("json", json_form), ("script", script_form)):
        old_f = fn(old)
        new_f = fn(new)
        if old_f == old and form_name != "html":
            # No quotes to escape; html and raw forms are identical.
            pass
        n = text.count(old_f)
        if n:
            text = text.replace(old_f, new_f)
            counts[form_name] = n
    return text, counts


def main() -> int:
    repo = Path(".").resolve()
    targets = [
        repo / "index.html",
        repo / "index.txt",
        repo / "__next._full.txt",
        repo / "__next.__PAGE__.txt",
    ]
    for path in targets:
        text = path.read_text(encoding="utf-8")
        before = text
        per_file: dict[str, dict] = {}
        for label, old, new in EDITS:
            text, counts = replace_all_forms(text, old, new, label)
            if counts:
                per_file[label] = counts
        if text != before:
            path.write_text(text, encoding="utf-8")
        print(f"{path.name}: {per_file}")

    # Mirror meta-description into all *.html and *_head.txt files (these are
    # tiny and only carry the head metadata).
    desc_old = "Mapping the manifold of LLM safety failures"
    desc_new = (
        "Quality-Diversity (MAP-Elites) red-teaming on Llama-3-8B, GPT-OSS-20B, "
        "and GPT-5-Mini. 25\u00d725 behavioral grid, Alignment Deviation across ten "
        "harm categories, basin persistence under continuous defenses."
    )
    # rglob does not follow symlinks, so the rethinking-evals/ shadow tree is
    # already skipped. We just need to gather every head/route payload file.
    head_targets: list[Path] = []
    for pattern in ("*.html", "__next._head.txt", "index.txt", "__next._full.txt"):
        head_targets.extend(repo.rglob(pattern))
    for p in sorted(set(head_targets)):
        text = p.read_text(encoding="utf-8")
        if desc_old in text:
            text = text.replace(desc_old, desc_new)
            p.write_text(text, encoding="utf-8")
            print(f"meta-description applied: {p.relative_to(repo)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
