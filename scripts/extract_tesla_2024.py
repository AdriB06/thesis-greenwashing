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
    "2024-extended-version-tesla-impact-report.pdf"
)

output_path = os.path.join(
    project_root,
    "data",
    "cleaned_text",
    "Tesla_2024_Sustainability_raw.txt"
)

# =========================
# DEFINE PAGE RANGES
# =========================

pages = (
    list(range(3, 13)) +      # 4–13
    list(range(19, 64)) +     # 20–64
    list(range(65, 79)) +     # 66–79
    list(range(88, 104)) +    # 89–104
    list(range(138, 186)) +   # 139–186
    list(range(187, 198))     # 188–198
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