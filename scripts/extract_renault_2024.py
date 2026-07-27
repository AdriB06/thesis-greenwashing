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
    "Renault_URD_2024_EN.pdf"
)

output_path = os.path.join(
    project_root,
    "data",
    "raw_text",
    "Renault_2024_Sustainability_raw.txt"
)

# =========================
# DEFINE PAGE RANGES
# =========================

pages = (
    list(range(82, 88)) +    # pages 83–88: climate overview, SD strategy, env policy
    list(range(117, 154)) +  # pages 118–154: E1 climate, E2 pollution, E3 water
    list(range(162, 183))    # pages 163–183: E5 circular economy, waste, taxonomy
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