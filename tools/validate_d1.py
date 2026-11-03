"""Validate the D1 specification (SD-008) and, when python-docx is available, its DOCX build.

Each check takes the spec text and returns a list of problem strings, so the
checks can be unit-tested against small fixtures (see tests/test_validate_d1.py).
"""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "docs/modeling/SD-008_MODEL_SPECIFICATION.md"
DOCX = ROOT / "deliverables/D1_Model_Research_and_Specifications/SD-008_Model_Research_and_Specifications.docx"

KEY_NAMES = {"cardholder_id", "card_id", "merchant_id", "transaction_id"}
EXPECTED_TABLES = {"cardholders", "cards", "merchants", "transactions", "fraud_labels"}


def section(md, start, end):
    match = re.search(rf"{start}\n(.*?)\n{end}", md, re.S)
    return match.group(1) if match else ""


def dictionary_rows(md):
    body = section(md, r"# 9 Data dictionary", r"# 10 ")
    lines = [l for l in body.splitlines() if l.startswith("|") and not re.match(r"^\|\s*:?-", l)]
    return [[c.strip() for c in line.split("|")[1:-1]] for line in lines][1:]  # drop header row


def reference_entries(md):
    body = section(md, r"# 12 References", r"# Appendix A")
    return [p.strip() for p in body.split("\n\n") if p.strip()]


def check_counts(md):
    problems = []
    rows = dictionary_rows(md)
    features = [r for r in rows if r[1] not in KEY_NAMES]
    relationships = re.findall(r"^\d+\. ", section(md, r"# 5 Explicit mathematical model", r"# 6 "), re.M)
    latent_rows = re.findall(r"^\| `latent_|^\| `true_fraud`", md, re.M)
    if {r[0] for r in rows} != EXPECTED_TABLES:
        problems.append(f"dictionary tables differ from {sorted(EXPECTED_TABLES)}")
    for label, got, want in (
        ("features", len(features), 38),
        ("relationships", len(relationships), 20),
        ("references", len(reference_entries(md)), 18),
        ("latent rows", len(latent_rows), 7),
    ):
        if got != want:
            problems.append(f"{label}: expected {want}, found {got}")
    return problems


ALIASES = {"Bangko Sentral ng Pilipinas": "BSP"}


def reference_keys(md):
    """(first-author name, year, letter) for each reference; organizations also get a short alias."""
    keys = []
    for entry in reference_entries(md):
        m = re.match(r"^(.+?)\s*\((?:[A-Za-z ,]+, )?(\d{4})([a-z]?)\)", entry)
        if not m:
            continue
        name = m.group(1).split(",")[0].strip().rstrip(".")
        keys.append((name, m.group(2), m.group(3)))
        if name in ALIASES:
            keys.append((ALIASES[name], m.group(2), m.group(3)))
    return keys


def check_citations(md):
    """Each reference must be cited in the body; each (Author, Year) citation must have a reference."""
    keys = reference_keys(md)
    body = md.split("# 12 References")[0]
    names = sorted({k[0] for k in keys}, key=len, reverse=True)
    problems = []
    for name, year, letter in keys:
        if name in ALIASES.values():
            continue
        alias = ALIASES.get(name)
        pattern = rf"(?:{re.escape(name)}|{re.escape(alias or name)})[^\n]{{0,60}}?\b{year}{letter}?\b"
        if not re.search(pattern, body):
            problems.append(f"reference never cited: {name} {year}{letter}")
    cited = re.findall(rf"({'|'.join(map(re.escape, names))})(?: et al\.)?,? \[?(?:BSP\],? )?\(?(\d{{4}})([a-z]?)", body)
    have = {(n, y, l) for n, y, l in keys}
    for name, year, letter in cited:
        if (name, year, letter) not in have and (name, year, "") not in have:
            problems.append(f"citation without reference: {name} {year}{letter}")
    for name, year, letter in keys:
        if letter and not any(k[0] == name and k[1] == year and k[2] != letter for k in keys):
            problems.append(f"orphan suffix: {name} {year}{letter}")
    return problems


def check_equation_numbers(md):
    numbers = [int(n) for n in re.findall(r"^(\d+)\. ", section(md, r"# 5 Explicit mathematical model", r"# 6 "), re.M)]
    if numbers != list(range(1, len(numbers) + 1)):
        return [f"equation numbering not contiguous: {numbers}"]
    return []


def check_dictionary_vs_erd(md):
    """Features named in the data dictionary must be unique per table."""
    seen, problems = set(), []
    for row in dictionary_rows(md):
        key = (row[0], row[1])
        if key in seen:
            problems.append(f"duplicate dictionary row: {row[0]}.{row[1]}")
        seen.add(key)
    return problems


def check_parameter_registry(md):
    """Greek parameters used in the equations should appear in the parameter registry section."""
    equations = section(md, r"# 5 Explicit mathematical model", r"# 6 ")
    registry = re.search(r"(?:parameter registry|Parameter registry)(.*?)(?:\n# )", md, re.S)
    if not registry:
        return ["parameter registry section not found"]
    used = set(re.findall(r"\\?(gamma|eta|rho|tau|kappa|omega|mu)_?\{?\w*\}?", equations))
    return [f"parameter {name} used in equations but absent from registry" for name in sorted(used) if name not in registry.group(1)]


CHECKS = (check_counts, check_citations, check_equation_numbers, check_dictionary_vs_erd, check_parameter_registry)


def check_docx(md):
    try:
        from docx import Document
    except ImportError:
        print("SKIP docx checks (python-docx not installed)")
        return []
    doc = Document(DOCX)
    text = "\n".join(p.text for p in doc.paragraphs)
    problems = []
    if len(doc.tables) < 4:
        problems.append("docx has fewer than 4 tables")
    if len(doc.inline_shapes) < 1:
        problems.append("docx has no inline images")
    for needle in ("SD-008 Model Research and Specifications", "Appendix G Final team review checklist"):
        if needle not in text:
            problems.append(f"docx missing: {needle}")
    if DOCX.stat().st_size <= 100_000:
        problems.append("docx smaller than 100 KB")
    return problems


def main():
    md = SPEC.read_text(encoding="utf-8")
    failed = False
    for check in (*CHECKS, check_docx):
        problems = check(md)
        status = "FAIL" if problems else "PASS"
        print(f"{status} {check.__name__}")
        for problem in problems:
            print(f"  - {problem}")
        failed = failed or bool(problems)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
