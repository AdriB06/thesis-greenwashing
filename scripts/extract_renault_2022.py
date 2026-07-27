import pdfplumber
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
    "Renault_urd_2022_en.pdf"
)

output_path = os.path.join(
    project_root,
    "data",
    "raw_text",
    "Renault_2022_Sustainability_raw.txt"
)

# =========================
# DEFINE PAGE RANGES
# =========================

pages = (
    list(range(164, 213)) +  # 165–213: full environmental chapter 2.3
    list(range(250, 265))    # 251–265: appendices, TCFD, site env indicators
)

# =========================
# EXTRACT TEXT (column-aware)
# =========================

full_text = ""

with pdfplumber.open(pdf_path) as pdf:
    for page_index in pages:
        page = pdf.pages[page_index]
        
        width = page.width
        
        # Split page into left and right columns
        left_bbox  = (0,          0, width / 2, page.height)
        right_bbox = (width / 2,  0, width,     page.height)
        
        left_text  = page.within_bbox(left_bbox).extract_text()  or ""
        right_text = page.within_bbox(right_bbox).extract_text() or ""
        
        # Combine columns top-to-bottom, left before right
        page_text = left_text + "\n" + right_text
        full_text += page_text + "\n\n"

# =========================
# SAVE OUTPUT
# =========================

with open(output_path, "w", encoding="utf-8") as f:
    f.write(full_text)

print("✅ Extraction complete.")
print(f"Pages extracted: {len(pages)}")
print(f"Saved to: {output_path}")