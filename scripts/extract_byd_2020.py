"""
BYD 2020 Sustainability Report — OCR Extraction
================================================
Image-based PDF with 2 pages per physical page in 2-column layout.
PyMuPDF cannot extract text directly → uses pdf2image + pytesseract OCR.

DEVIATION FROM STANDARD PIPELINE:
This script uses OCR instead of direct text extraction because the BYD 2020
Sustainability Report is an image-based PDF with no selectable text layer.
This deviation is documented at filename, code comment, and thesis methodology levels.

INSTALL (once):
    pip install pdf2image pytesseract pillow --break-system-packages
    Install Tesseract OCR engine: https://github.com/UB-Mannheim/tesseract/wiki
"""

import os
import re
from pathlib import Path
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# =========================
# PATH SETUP
# =========================

base_dir = Path(__file__).resolve().parent
project_root = base_dir.parent

pdf_path = project_root / "data" / "raw_pdfs" / "BYD_sustainability_report_2020.pdf"

output_path = project_root / "data" / "raw_text" / "BYD_2020_Sustainability_raw.txt"

# =========================
# DEFINE PAGE RANGES
# =========================

pages = (
    list(range(0, 1)) +     # PDF p.1: President's letter
    list(range(27, 34)) +   # PDF p.28-34: Green Operation & Technology
    list(range(38, 40))     # PDF p.39-40: Looking Forward + GRI Index
)

# =========================
# OCR EXTRACTION
# =========================

def clean_ocr_text(text: str) -> str:
    """Clean OCR artifacts from image-based PDF extraction."""
    # Remove CJK characters (Chinese headers/footers)
    text = re.sub(r'[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]', '', text)
    # Collapse multiple spaces and newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()

try:
    from pdf2image import convert_from_path
    import pytesseract
    from PIL import Image

    print(f"📄 Opening: {pdf_path}")
    print(f"🔍 OCR mode: image-based PDF detected")
    print(f"📑 Pages to process: {len(pages)}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    all_text = []
    errors = 0

    for page_num in pages:
        try:
            # Convert single PDF page to image at 300 DPI for good OCR quality
            images = convert_from_path(
                str(pdf_path),
                dpi=300,
                first_page=page_num + 1,  # pdf2image uses 1-indexed pages
                last_page=page_num + 1
            )

            if not images:
                print(f"⚠️  No image generated for page {page_num + 1}")
                errors += 1
                continue

            img = images[0]

            # Since each physical page contains 2 printed pages side by side,
            # split the image vertically and OCR each half separately
            width, height = img.size
            left_half  = img.crop((0,         0, width // 2, height))
            right_half = img.crop((width // 2, 0, width,     height))

            text_left  = pytesseract.image_to_string(left_half,  lang='eng')
            text_right = pytesseract.image_to_string(right_half, lang='eng')

            combined = clean_ocr_text(text_left + "\n" + text_right)

            all_text.append(f"--- Page {page_num + 1} ---\n{combined}\n")
            print(f"✅ Page {page_num + 1} extracted ({len(combined)} chars)")

        except Exception as e:
            print(f"⚠️  Error on page {page_num + 1}: {e}")
            errors += 1
            continue

    # Save output
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(all_text))

    print(f"\n{'='*60}")
    print(f"✅ OCR extraction complete")
    print(f"   Pages extracted: {len(pages) - errors}/{len(pages)}")
    print(f"   Errors: {errors}")
    print(f"   Saved to: {output_path}")
    print(f"{'='*60}")

except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Install with: pip install pdf2image pytesseract pillow --break-system-packages")
    print("Also install Tesseract OCR: https://github.com/UB-Mannheim/tesseract/wiki")