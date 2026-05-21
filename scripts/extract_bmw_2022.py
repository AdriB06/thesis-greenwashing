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
    "BMW-Group-Report-2022-en.pdf"
)

output_path = os.path.join(
    project_root,
    "data",
    "raw_text",
    "BMW_2022_Sustainability_raw.txt"
)

# =========================
# DEFINE PAGE RANGES
# =========================
# Environmental/Climate Sustainability Sections Only
# Comparable to 2024 ESRS Environmental Information

pages = (
    list(range(40, 50)) +     # 41-50: BMW Group Integrated Strategy
    list(range(78, 89)) +     # 79-89: EU Taxonomy
    list(range(89, 102)) +    # 90-102: Products (Carbon Emissions, Electromobility)
    list(range(102, 113))     # 103-113: Production & Supplier Network (Circular Economy)
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

print("✅ BMW 2022 extraction complete.")
print(f"Pages extracted: {len(pages)} pages")
print(f"Page ranges: 41-50 (Strategy), 79-89 (Taxonomy), 90-102 (Products), 103-113 (Production)")
print(f"Saved to: {output_path}")