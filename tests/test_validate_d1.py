import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import validate_d1 as v  # noqa: E402

SPEC = Path(__file__).resolve().parents[1] / "docs/modeling/SD-008_MODEL_SPECIFICATION.md"

MINI = """# 5 Explicit mathematical model
1. a
2. b
# 6 x
# 9 Data dictionary
| table | column |
|---|---|
| cards | card_id |
| cards | limit |
# 10 x
# 12 References
Smith, A. (2020). Title.

Bangko Sentral ng Pilipinas. (2025a). Report.
# Appendix A x
"""


def test_equation_numbering_detects_gap():
    assert v.check_equation_numbers(MINI) == []
    assert v.check_equation_numbers(MINI.replace("2. b", "3. b"))


def test_duplicate_dictionary_row_detected():
    dup = MINI.replace("| cards | limit |", "| cards | card_id |")
    assert v.check_dictionary_vs_erd(dup)
    assert v.check_dictionary_vs_erd(MINI) == []


def test_orphan_suffix_and_uncited_reference_detected():
    problems = v.check_citations("Intro text.\n" + MINI)
    assert any("never cited" in p for p in problems)
    assert any("orphan suffix" in p for p in problems)


def test_citation_without_reference_detected():
    body = "Smith et al. (2019) say things.\n" + MINI
    assert any("citation without reference" in p for p in v.check_citations(body))


def test_real_spec_citations_and_numbering_are_consistent():
    md = SPEC.read_text(encoding="utf-8")
    assert v.check_citations(md) == []
    assert v.check_equation_numbers(md) == []
    assert v.check_counts(md) == []
