from pathlib import Path
import re

from PIL import Image, ImageDraw, ImageFont
from docx import Document
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs/modeling/SD-008_MODEL_SPECIFICATION.md"
OUTPUT = ROOT / "deliverables/D1_Model_Research_and_Specifications/SD-008_Model_Research_and_Specifications.docx"
ERD = ROOT / "deliverables/D1_Model_Research_and_Specifications/assets/SD-008_ERD.png"


def font(size, bold=False):
    candidates = (
        ("arialbd.ttf", "LiberationSans-Bold.ttf", "DejaVuSans-Bold.ttf", "/usr/share/fonts/noto/NotoSans-Bold.ttf")
        if bold
        else ("arial.ttf", "LiberationSans-Regular.ttf", "DejaVuSans.ttf", "/usr/share/fonts/noto/NotoSans-Regular.ttf")
    )
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def build_erd():
    image = Image.new("RGB", (1800, 1120), "white")
    draw = ImageDraw.Draw(image)
    title_font, entity_font, field_font = font(34, True), font(24, True), font(18)
    draw.text((900, 28), "SD-008 Analyst-Facing Data Model", anchor="ma", fill="#172B4D", font=title_font)
    boxes = {
        "CARDHOLDERS": (60, 130, 520, 475, ["PK cardholder_id", "age_band", "income_band", "home_region", "urbanicity", "account_open_date", "employment_segment"]),
        "CARDS": (670, 130, 1130, 475, ["PK card_id", "FK cardholder_id", "card_brand", "issue_date", "expiry_date", "credit_limit_php", "card_status", "product_tier"]),
        "MERCHANTS": (60, 675, 520, 1020, ["PK merchant_id", "merchant_category", "mcc", "country_code", "merchant_region", "merchant_size_band", "online_capable"]),
        "TRANSACTIONS": (670, 575, 1190, 1080, ["PK transaction_id", "FK card_id", "FK merchant_id", "transaction_ts", "amount_php", "channel", "foreign_transaction", "authorization_status", "entry_mode", "device_trust_level", "distance_from_home_km", "chronological behavior features"]),
        "FRAUD_LABELS": (1320, 610, 1740, 990, ["PK/FK transaction_id", "observed_fraud", "review_status", "fraud_type", "alert_ts", "review_ts", "label_source", "sparse: missing means unknown"]),
    }
    for name, (x1, y1, x2, y2, fields) in boxes.items():
        draw.rounded_rectangle((x1, y1, x2, y2), 18, fill="#F5F8FC", outline="#3567A8", width=4)
        draw.rounded_rectangle((x1, y1, x2, y1 + 58), 18, fill="#173F73", outline="#173F73")
        draw.rectangle((x1, y1 + 40, x2, y1 + 58), fill="#173F73")
        draw.text(((x1 + x2) / 2, y1 + 29), name, anchor="mm", fill="white", font=entity_font)
        y = y1 + 78
        for field in fields:
            fill = "#8B2E2E" if field.startswith("sparse") else "#1F2937"
            draw.text((x1 + 22, y), field, fill=fill, font=field_font)
            y += 33
    def line(points, label):
        draw.line(points, fill="#3567A8", width=5)
        mx = sum(p[0] for p in points) / len(points)
        my = sum(p[1] for p in points) / len(points)
        draw.rounded_rectangle((mx - 80, my - 18, mx + 80, my + 18), 8, fill="white")
        draw.text((mx, my), label, anchor="mm", fill="#173F73", font=field_font)
    line([(520, 300), (670, 300)], "1 to 1..N")
    line([(900, 475), (900, 575)], "1 to 0..N")
    line([(520, 845), (670, 845)], "1 to 0..N")
    line([(1190, 825), (1320, 825)], "1 to 0..1")
    image.save(ERD, dpi=(180, 180))


def shade_cell(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def set_cell_margins(cell, top=70, start=90, bottom=70, end=90):
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for margin, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = OxmlElement(f"w:{margin}")
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")
        tc_mar.append(node)


def strip_math_parens(text):
    """Drop outer parens of a math group like ' (Y_{k}=1)'; keep call parens and plain '(i)'."""
    out, i = [], 0
    while i < len(text):
        if text[i] == "(" and (i == 0 or text[i - 1].isspace()):
            depth, j = 0, i
            while j < len(text):
                depth += (text[j] == "(") - (text[j] == ")")
                if depth == 0:
                    break
                j += 1
            inner = text[i + 1 : j]
            if depth == 0 and re.search(r"[\\_^]", inner):
                out.append(inner)
                i = j + 1
                continue
        out.append(text[i])
        i += 1
    return "".join(out)


_SCRIPT_RE = re.compile(
    r"(?<![A-Za-z0-9_])(logit|[A-Za-zΑ-ω])((?:[_^](?:\{[^}]*\}|-?[A-Za-z0-9](?![A-Za-z])))+)"
)


def math_segments(text):
    """Split text into (kind, text) with kind '' / 'sub' / 'sup'; only single-letter bases."""
    segs, pos = [], 0
    for m in _SCRIPT_RE.finditer(text):
        segs.append(("", text[pos : m.start()] + m.group(1)))
        for op, body in re.findall(r"([_^])(\{[^}]*\}|-?[A-Za-z0-9])", m.group(2)):
            segs.append(("sub" if op == "_" else "sup", body.strip("{}")))
        pos = m.end()
    segs.append(("", text[pos:]))
    return [(k, t) for k, t in segs if t]


def add_math_runs(paragraph, text, bold=False):
    for kind, chunk in math_segments(text):
        run = paragraph.add_run(chunk)
        run.font.subscript = kind == "sub" or None
        run.font.superscript = kind == "sup" or None
        run.bold = bold or None


def add_lead_runs(paragraph, line):
    if line.startswith("**") and "**" in line[2:]:
        lead, _, rest = line[2:].partition("**")
        add_math_runs(paragraph, clean_inline(lead), bold=True)
        line = rest
    add_math_runs(paragraph, clean_inline(line))


def is_display_formula(line):
    s = line.strip().rstrip(".")
    if not (s.startswith("(") and s.endswith(")")):
        return False
    depth = 0
    for k, ch in enumerate(s):
        depth += (ch == "(") - (ch == ")")
        if depth == 0 and k < len(s) - 1:
            return False
    return True


def clean_inline(text):
    text = strip_math_parens(re.sub(r"[`*]", "", text).replace("\\(", "").replace("\\)", ""))
    symbols = {
        "\\lambda": "λ", "\\Lambda": "Λ", "\\sigma": "σ", "\\theta": "θ", "\\omega": "ω",
        "\\epsilon": "ε", "\\kappa": "κ", "\\alpha": "α", "\\beta": "β",
        "\\gamma": "γ", "\\delta": "δ", "\\Delta": "Δ", "\\eta": "η",
        "\\rho": "ρ", "\\phi": "φ", "\\mu": "μ", "\\tau": "τ",
        "\\pi": "π", "\\sum": "Σ", "\\sim": "~", "\\in": "∈",
        "\\bar": "bar", "\\hat": "hat ", "\\ne": "≠", "\\mid": "|", "\\,": "",
    }
    for source, target in symbols.items():
        text = text.replace(source, target)
    return text.replace("\\", "")


def add_table(doc, rows, wide=False):
    table = doc.add_table(rows=1, cols=len(rows[0]))
    table.style = "Table Grid"
    table.autofit = True
    for j, value in enumerate(rows[0]):
        cell = table.rows[0].cells[j]
        add_math_runs(cell.paragraphs[0], clean_inline(value))
        shade_cell(cell, "173F73")
        for run in cell.paragraphs[0].runs:
            run.font.bold = True
            run.font.color.rgb = RGBColor(255, 255, 255)
            run.font.size = Pt(6.5 if wide else 8)
    table.rows[0]._tr.get_or_add_trPr().append(OxmlElement("w:tblHeader"))
    for i, row in enumerate(rows[1:], start=1):
        cells = table.add_row().cells
        for j, value in enumerate(row):
            add_math_runs(cells[j].paragraphs[0], clean_inline(value))
            cells[j].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            if i % 2 == 0:
                shade_cell(cells[j], "EFF4FA")
            for paragraph in cells[j].paragraphs:
                paragraph.paragraph_format.space_after = Pt(0)
                paragraph.paragraph_format.line_spacing = 1.0
                for run in paragraph.runs:
                    run.font.size = Pt(6 if wide else 7.5)
            set_cell_margins(cells[j], 55 if wide else 75, 65 if wide else 90, 55 if wide else 75, 65 if wide else 90)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def set_landscape(section):
    section.orientation = WD_ORIENT.LANDSCAPE
    section.page_width, section.page_height = Inches(11.7), Inches(8.3)
    section.left_margin = section.right_margin = Inches(0.42)
    section.top_margin = section.bottom_margin = Inches(0.55)


def set_portrait(section):
    section.orientation = WD_ORIENT.PORTRAIT
    section.page_width, section.page_height = Inches(8.3), Inches(11.7)
    section.left_margin = section.right_margin = Inches(0.78)
    section.top_margin = section.bottom_margin = Inches(0.72)


def build_docx():
    text = SOURCE.read_text(encoding="utf-8")
    lines = text.splitlines()
    doc = Document()
    set_portrait(doc.sections[0])
    styles = doc.styles
    styles["Normal"].font.name = "Aptos"
    styles["Normal"].font.size = Pt(9.5)
    styles["Normal"].paragraph_format.space_after = Pt(5)
    styles["Normal"].paragraph_format.line_spacing = 1.08
    for name, size in (("Title", 26), ("Heading 1", 17), ("Heading 2", 12.5)):
        style = styles[name]
        style.font.name = "Aptos Display"
        style.font.size = Pt(size)
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.font.bold = True
    styles["Heading 1"].paragraph_format.page_break_before = True
    styles["Heading 1"].paragraph_format.space_after = Pt(8)
    styles["Heading 2"].paragraph_format.keep_with_next = True
    styles["Heading 2"].paragraph_format.space_before = Pt(8)
    styles["Heading 2"].paragraph_format.space_after = Pt(4)

    title = doc.add_paragraph(style="Title")
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.add_run("SD-008 Model Research and Specifications")
    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle.add_run("Credit Card Fraud Detection\nDeliverable 1 Technical Draft").bold = True
    doc.add_paragraph("Eskwelabs Innovation Fellowship Data Innovation Track").alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph("Prepared 1 November 2026\nStatus  Submission candidate pending team review").alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_page_break()
    doc.add_heading("Contents", level=1)
    for line in lines:
        if line.startswith("# ") and not line.startswith("# SD-008"):
            p = doc.add_paragraph(clean_inline(line[2:]), style="List Bullet")
            p.paragraph_format.space_after = Pt(0)
            for run in p.runs:
                run.font.size = Pt(8)
        elif line.startswith("## "):
            p = doc.add_paragraph(clean_inline(line[3:]))
            p.paragraph_format.left_indent = Inches(0.25)
            p.paragraph_format.space_after = Pt(0)
            for run in p.runs:
                run.font.size = Pt(8)
    doc.add_page_break()

    i, in_code, code_lines, skip_title, current_heading = 0, False, [], True, ""
    while i < len(lines):
        line = lines[i]
        if skip_title and line.startswith("# SD-008"):
            i += 1
            continue
        skip_title = False
        if line.startswith("```"):
            if not in_code:
                in_code, code_lines = True, []
            else:
                in_code = False
                if code_lines and code_lines[0].strip() == "erDiagram":
                    p = doc.add_paragraph()
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    p.add_run().add_picture(str(ERD), width=Inches(6.5))
                    cap = doc.add_paragraph("Figure 1  SD-008 analyst-facing entity relationship model")
                    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    cap.runs[0].italic = True
                else:
                    p = doc.add_paragraph("\n".join(code_lines))
                    p.style = styles["Normal"]
            i += 1
            continue
        if in_code:
            code_lines.append(line)
            i += 1
            continue
        if line.startswith("| "):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                values = [v.strip() for v in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-+:?", v) for v in values):
                    rows.append(values)
                i += 1
            if rows:
                wide = len(rows[0]) > 7
                if wide and current_heading != "9 Data dictionary":
                    set_landscape(doc.add_section(WD_SECTION.NEW_PAGE))
                add_table(doc, rows, wide)
                if wide:
                    set_portrait(doc.add_section(WD_SECTION.NEW_PAGE))
            continue
        if line.startswith("# "):
            current_heading = clean_inline(line[2:])
            if current_heading == "9 Data dictionary":
                set_landscape(doc.add_section(WD_SECTION.NEW_PAGE))
            h = doc.add_heading(current_heading, level=1)
            if current_heading.startswith("Appendix") and not current_heading.startswith("Appendix A"):
                h.paragraph_format.page_break_before = False
        elif line.startswith("## "):
            doc.add_heading(clean_inline(line[3:]), level=2)
        elif re.match(r"^\d+[a-z]?\. ", line):
            num, _, body = line.partition(" ")
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.3)
            p.paragraph_format.first_line_indent = Inches(-0.3)
            p.add_run(num + " ")
            add_lead_runs(p, body)
        elif line.startswith("- [ ] "):
            doc.add_paragraph("☐ " + clean_inline(line[6:]))
        elif line.startswith("- "):
            doc.add_paragraph(clean_inline(line[2:]), style="List Bullet")
        elif line.strip():
            p = doc.add_paragraph()
            add_lead_runs(p, line)
            if current_heading == "12 References":
                p.paragraph_format.left_indent = Inches(0.25)
                p.paragraph_format.first_line_indent = Inches(-0.25)
                p.paragraph_format.space_after = Pt(4)
                for run in p.runs:
                    run.font.size = Pt(8)
            if is_display_formula(line):
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        i += 1

    for section in doc.sections:
        footer = section.footer.paragraphs[0]
        footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
        footer.text = "SD-008 Deliverable 1  |  Submission candidate  |  Page "
        field = OxmlElement("w:fldSimple")
        field.set(qn("w:instr"), "PAGE")
        footer._p.append(field)
        for run in footer.runs:
            run.font.size = Pt(8)
            run.font.color.rgb = RGBColor(90, 90, 90)
    doc.core_properties.title = "SD-008 Model Research and Specifications"
    doc.core_properties.subject = "Deliverable 1 technical draft"
    doc.core_properties.author = "SD-008 Team"
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUTPUT)


if __name__ == "__main__":
    build_erd()
    build_docx()
    print(OUTPUT)
