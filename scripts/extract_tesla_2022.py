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
    "2022-tesla-impact-report.pdf"
)

output_path = os.path.join(
    project_root,
    "data",
    "raw_text",
    "Tesla_2022_Sustainability_raw.txt"
)

# =========================
# DEFINE PAGE RANGES
# =========================

pages = (
    list(range(4, 16)) +      # 5–16
    list(range(16, 58)) +     # 17–58
    list(range(58, 70)) +     # 59–70
    list(range(89, 97)) +     # 90–97
    list(range(136, 191)) +   # 137–191
    list(range(191, 202)) +   # 192–202
    list(range(202, 215))     # 203–215
)

# =========================
# EXTRACT TEXT
# =========================

text = extract_text(pdf_path, page_numbers=pages)

# =========================
# SAVE OUTPUT
# =========================

with open(output_path, "w", encoding="utf-8") as f:
    f.write(text)

print("✅ Extraction complete.")
print(f"Pages extracted: {len(pages)}")
print(f"Saved to: {output_path}")
