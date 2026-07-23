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
    "BYD_sustainability_report_2020.pdf"
)

output_path = os.path.join(
    project_root,
    "data",
    "raw_text",
    "BYD_2020_Sustainability_raw.txt"
)

# =========================
# DEFINE PAGE RANGES
# =========================

pages = (
    list(range(27, 33)) +    # 28-33
    list(range(38, 39))    # 39
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