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
    "BMW-Group-Report-2024-en.pdf"
)

output_path = os.path.join(
    project_root,
    "data",
    "cleaned_text",
    "BMW_2024_Sustainability_raw.txt"
)

# =========================
# DEFINE PAGE RANGES
# =========================

pages = (
    list(range(90, 92)) +     # 91–92
    list(range(94, 158)) +    # 95–158
    list(range(193, 197))     # 194–197
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