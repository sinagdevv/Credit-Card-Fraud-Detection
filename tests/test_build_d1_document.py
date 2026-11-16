import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import build_d1_document as b  # noqa: E402

SPEC = Path(__file__).resolve().parents[1] / "docs/modeling/SD-008_MODEL_SPECIFICATION.md"


@pytest.mark.parametrize("text,expected", [
    ("use (Y_{true,k}=1) now", "use Y_{true,k}=1 now"),
    ("cardholders (i) and (j<k)", "cardholders (i) and (j<k)"),
    ("draw Categorical(\\pi_R)", "draw Categorical(\\pi_R)"),
    ("apply softmax_j(x)", "apply softmax_j(x)"),
])
def test_strip_math_parens(text, expected):
    assert b.strip_math_parens(text) == expected


def test_strip_math_parens_negative():
    assert b.strip_math_parens("use (Y_k=1) now") != "use (Y_k=1) now"


@pytest.mark.parametrize("text,expected", [
    ("A_k", [("", "A"), ("sub", "k")]),
    ("u_{j,A}", [("", "u"), ("sub", "j,A")]),
    ("σ_L^2", [("", "σ"), ("sub", "L"), ("sup", "2")]),
    ("logit^-1(x)", [("", "logit"), ("sup", "-1"), ("", "(x)")]),
])
def test_math_segments(text, expected):
    assert b.math_segments(text) == expected


@pytest.mark.parametrize("name", [
    "spend_deviation_z_k", "tx_count_prev_1h", "credit_limit_php",
    "cardholder_id", "pi_R", "x_ab",
])
def test_field_names_untouched(name):
    assert b.math_segments(name) == [("", name)]


def test_roundtrip_examples():
    join = lambda s: "".join(t for _, t in b.math_segments(s))
    assert join("A_k") == "Ak"
    assert join("u_{j,A}") == "uj,A"
    assert join("σ_L^2") == "σL2"
    assert join("credit_limit_php") == "credit_limit_php"


def test_clean_inline_no_backslash():
    assert b.clean_inline("(R_i \\sim Categorical(\\pi_R))") == "R_i ~ Categorical(π_R)"


def test_is_display_formula():
    assert b.is_display_formula("(p_k=logit^-1(\\beta_0+x))")
    assert not b.is_display_formula("Indices are cardholders (i), cards (c).")


def test_spec_wide_no_markup_leaks():
    in_code, bad = False, []
    for line in SPEC.read_text(encoding="utf-8").splitlines():
        if line.startswith("```"):
            in_code = not in_code
            continue
        if in_code or line.lstrip().startswith("|"):
            continue
        out = "".join(t for _, t in b.math_segments(b.clean_inline(line)))
        if "\\" in out or "_{" in out or "^{" in out:
            bad.append(line)
    assert not bad, bad[:5]
