import re
import os
from pathlib import Path

# =========================
# PATHS
# =========================
project_root = Path(__file__).resolve().parent.parent

input_path = project_root / "data" / "raw_pdfs" / \
             "BYD_sustainability_report_2020_pdf.txt"

output_path = project_root / "data" / "raw_text" / \
              "BYD_2020_Sustainability_raw.txt"

# =========================
# PAGES TO EXTRACT
# (these are the printed page numbers 
#  as they appear in the text file)
# =========================

TARGET_PAGES = [30, 31, 32, 33, 34, 35,  # Green Operation
                36, 37,                    # Green Technology
                41,                        # Looking Forward
                42, 43]                    # GRI Index

# =========================
# PARSE TEXT BY PAGE MARKERS
# =========================

def extract_pages_from_text(filepath, target_pages):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split on page markers
    # Matches: ===== Page X =====
    pattern = r'={5}\s*Page\s+(\d+)\s*={5}'
    parts = re.split(pattern, content)

    # parts alternates: [text_before, page_num, text, page_num, text...]
    pages = {}
    for i in range(1, len(parts) - 1, 2):
        page_num = int(parts[i])
        page_text = parts[i + 1].strip()
        pages[page_num] = page_text

    # Extract only target pages
    extracted = []
    for page in target_pages:
        if page in pages:
            extracted.append(f"===== Page {page} =====\n{pages[page]}")
        else:
            print(f"⚠️  Page {page} not found in text file")

    return "\n\n".join(extracted)

# =========================
# CLEAN TEXT
# =========================

def clean_text(text):
    import re
    # Remove CJK characters
    text = re.sub(
        r'[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]',
        '', text
    )
    # Collapse whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()

# =========================
# RUN
# =========================

output_path.parent.mkdir(parents=True, exist_ok=True)

extracted = extract_pages_from_text(input_path, TARGET_PAGES)
cleaned = clean_text(extracted)

with open(output_path, 'w', encoding='utf-8') as f:
    f.write(cleaned)

print(f"✅ Extraction complete")
print(f"   Pages extracted: {TARGET_PAGES}")
print(f"   Saved to: {output_path}")