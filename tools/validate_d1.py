from pathlib import Path
import re
from docx import Document

root = Path(__file__).resolve().parents[1]
md = (root / "docs/modeling/SD-008_MODEL_SPECIFICATION.md").read_text(encoding="utf-8")
docx_path = root / "deliverables/D1_Model_Research_and_Specifications/SD-008_Model_Research_and_Specifications.docx"
doc = Document(docx_path)
doc_text = "\n".join(p.text for p in doc.paragraphs)

dictionary = re.search(r"# 9 Data dictionary\n(.*?)\n# 10 ", md, re.S).group(1)
rows = [line.split("|")[1:-1] for line in dictionary.splitlines() if line.startswith("| ")][2:]
key_names = {"cardholder_id", "card_id", "merchant_id", "transaction_id"}
features = [r for r in rows if r[1].strip() not in key_names]
tables = {r[0].strip() for r in rows}
section_five = re.search(r"# 5 Explicit mathematical model\n(.*?)\n# 6 ", md, re.S).group(1)
relationships = re.findall(r"^\d+\. ", section_five, re.M)
references = re.search(r"# 12 References\n(.*?)\n# Appendix A", md, re.S).group(1)
reference_count = len([p for p in references.split("\n\n") if p.strip()])
latent_rows = re.findall(r"^\| `latent_|^\| `true_fraud`", md, re.M)

assert tables == {"cardholders", "cards", "merchants", "transactions", "fraud_labels"}
assert len(features) == 38, len(features)
assert len(relationships) == 20, len(relationships)
assert reference_count == 18, reference_count
assert len(latent_rows) == 7, len(latent_rows)
assert len(doc.tables) >= 4
assert len(doc.inline_shapes) >= 1
assert "SD-008 Model Research and Specifications" in doc_text
assert "Appendix G Final team review checklist" in doc_text
assert docx_path.stat().st_size > 100_000
print(f"PASS tables={len(tables)} features={len(features)} relationships={len(relationships)} references={reference_count} latents={len(latent_rows)} docx_tables={len(doc.tables)} images={len(doc.inline_shapes)} sections={len(doc.sections)}")
