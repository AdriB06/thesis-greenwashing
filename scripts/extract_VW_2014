from pdfminer.high_level import extract_text
import os

# =========================
# PATH SETUP
# =========================

base_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(base_dir)

pdf_path = os.path.join(
    project_root,
    "data",
    "raw_pdfs",
    "2014-Annual-Report.pdf"
)

output_path = os.path.join(
    project_root,
    "data",
    "raw_text",
    "VW_2014_Sustainability_raw.txt"
)

# =========================
# DEFINE PAGE RANGES
# =========================

pages = list(range(150, 185))     # 150-184

# =========================
# EXTRACT TEXT
# =========================

text = extract_text(pdf_path, page_numbers=pages)

# =========================
# SAVE OUTPUT
# =========================

with open(output_path, "w", encoding="utf-8") as f:
    f.write(text)

print("✅ VW 2014 extraction complete.")
print(f"Pages extracted: {len(pages)} pages")
print(f"Page ranges: 150-184")
print(f"Saved to: {output_path}")