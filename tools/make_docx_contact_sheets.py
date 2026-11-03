import sys
from pathlib import Path
from PIL import Image, ImageDraw

# Usage: make_docx_contact_sheets.py [folder-with-page-*.png]
qa = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / ".qa/d1-final"
pages = sorted(qa.glob("page-*.png"))
for start in range(0, len(pages), 6):
    subset = pages[start:start + 6]
    thumbs = []
    for page in subset:
        image = Image.open(page).convert("RGB")
        image.thumbnail((520, 720))
        thumbs.append((page.stem, image.copy()))
    sheet = Image.new("RGB", (1080, 2220), "#D9D9D9")
    draw = ImageDraw.Draw(sheet)
    for index, (name, image) in enumerate(thumbs):
        x = 10 + (index % 2) * 535
        y = 30 + (index // 2) * 730
        draw.text((x, y - 22), name, fill="black")
        sheet.paste(image, (x, y))
    sheet.save(qa / f"contact-{start + 1:02d}-{start + len(subset):02d}.png")
