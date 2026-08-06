import re
import os

# ==================================================
# PATHS
# ==================================================

base_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(base_dir)

input_path = os.path.join(
    project_root,
    "data",
    "raw_text",
    "BYD_2020_Sustainability_raw.txt"
)

output_path = os.path.join(
    project_root,
    "data",
    "cleaned_text",
    "BYD_2020_Sustainability_clean.txt"
)

# ==================================================
# LOAD RAW TEXT
# ==================================================

with open(input_path, "r", encoding="utf-8") as f:
    text = f.read()

# ==================================================
# STEP 1: NORMALIZE PDF ARTIFACTS
# ==================================================

# Remove page markers added during extraction
text = re.sub(r'={5}\s*Page\s*\d+\s*={5}', '', text)

# Convert form feed/page break to newline
text = text.replace("\x0c", "\n")

# Remove arrow symbols often produced by PDF extraction
text = text.replace("↗", " ")

# Fix common weird spaces
text = text.replace("\u00a0", " ")
text = text.replace("\u2009", " ")
text = text.replace("\u202f", " ")

# Remove OCR garbage fragments specific to BYD 2020 image extraction
text = re.sub(r'en Ms \d+', '', text)
text = re.sub(r'=e\s', '', text)
text = re.sub(r'¢', '', text)
text = re.sub(r'\bacters\b', 'meters', text)
text = re.sub(r',,::\.', '.', text)

# ==================================================
# STEP 2: FIX HYPHENATED LINE BREAKS
# Example: "envi-\nronment" -> "environment"
# ==================================================

text = re.sub(r'-\s*\n\s*', '', text)

# ==================================================
# STEP 3: SPLIT INTO LINES
# ==================================================

lines = text.splitlines()

# ==================================================
# HELPERS
# ==================================================

HEADER_PATTERNS = [
    "BYD Group Report 2020",
    "2020 BYD Corporate Social Responsibility Report",
    "To Our Stakeholders",
    "Combined Management Report",
    "Group Financial Statements",
    "Responsibility Statement and Auditor's Report",
    "Remuneration Report",
    "Other Information",
    "Sustainability Statement"
]

CONTENTS_HINTS = [
    "General Basis for Preparation of the Sustainability Statement",
    "Materiality Assessment",
    "Stakeholder Engagement",
    "Climate Change Mitigation and Adaption",
    "Climate Change Mitigation and Adaptation",
    "Holistic Environmental Management within the BYD Group",
    "Energy Efficiency and renewable Energy",
    "Reduction of Environmental Pollution",
    "Responsible Use of Water Resources",
    "Commitment to protecting Biodiversity",
    "Circular Economy and Resource Use",
    "EU Taxonomy",
    "Glossary and Explanation of Key Figures",
    "List of material Impacts, Risks and Opportunities",
    "ESRS-Index"
]

STANDALONE_NOISE = {
    "Quantity",
    "Waste Type",
    "YoY Growth",
    "Domestic",
    "waste",
    "Resources 2020 YoY Growth",
    "Building a green park",
    "Solid Waste in the Past 2 Years",
    "BYD energy/resource consumption for the past 2 years",
    "Greenhouse gas emission in 2020",
    "Recycling and reuse of waste",
    "Energy conservation",
    "Water and Gas Waste Discharge in the Past 2 Years",
    "New energy",
    "Solar products",
    "Rail business",
    "Green technology",
    "Sustainability products",
    "Energy Storage Products",
    "New Energy Vehicles",
}


def is_page_number(line: str) -> bool:
    return bool(re.fullmatch(r"\d{1,3}", line.strip()))


def is_report_header(line: str) -> bool:
    stripped = line.strip()
    return any(h in stripped for h in HEADER_PATTERNS)


def is_spaced_caps(line: str) -> bool:
    return bool(re.fullmatch(r'(?:[A-Z]\s+){5,}[A-Z]', line.strip()))


def is_all_caps_title(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    letters = re.sub(r'[^A-Za-z]', '', stripped)
    if len(letters) < 6:
        return False
    uppercase_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
    return uppercase_ratio > 0.9 and len(stripped) < 140 and len(stripped.split()) >= 3


def is_contents_entry(line: str) -> bool:
    stripped = line.strip()
    if re.match(r'^\d{1,3}\s+[A-Z]', stripped):
        return True
    if any(hint in stripped for hint in CONTENTS_HINTS):
        if not re.search(r'[.!?]$', stripped):
            return True
    return False


def is_table_noise(line: str) -> bool:
    stripped = line.strip()

    if len(stripped) <= 3:
        return True

    if stripped.lower().startswith("dummy "):
        return True

    # Mostly symbols/numbers
    if re.fullmatch(r'[\d\s\-–—./,%()]+', stripped):
        return True

    # Standalone noise labels
    if stripped in STANDALONE_NOISE:
        return True

    # Table rows containing units but no real prose verb
    if re.search(r'\b(Tonnes|kwh|cubic|liters|meters|billioncubic|Billion|Million|Standard)\b', stripped):
        if not re.search(r'[a-z]{6,}', stripped.lower()):
            return True

    return False


def looks_like_sentence_continuation(prev_line: str, next_line: str) -> bool:
    if not prev_line or not next_line:
        return False

    prev = prev_line.rstrip()
    nxt = next_line.lstrip()

    # If previous ends with sentence punctuation, keep newline
    if re.search(r'[.!?:;]$', prev):
        return False

    # If previous ends with a number or percentage, it's a table row — don't merge
    if re.search(r'[\d%]$', prev):
        return False

    # If next starts lowercase, it likely continues
    if re.match(r'^[a-z]', nxt):
        return True

    # If previous ends with comma or open bracket, likely continues
    if re.search(r'[,(\-]$', prev):
        return True

    return False


# ==================================================
# STEP 4: REMOVE STRUCTURAL NOISE
# ==================================================

filtered_lines = []

for line in lines:
    stripped = line.strip()

    if not stripped:
        filtered_lines.append("")
        continue

    if is_page_number(stripped):
        continue

    if is_report_header(stripped):
        continue

    if is_spaced_caps(stripped):
        continue

    if is_all_caps_title(stripped):
        continue

    if is_contents_entry(stripped):
        continue

    if is_table_noise(stripped):
        continue

    filtered_lines.append(stripped)

# ==================================================
# STEP 5: CLEAN EMPTY BLOCKS
# ==================================================

compressed_lines = []
previous_blank = False

for line in filtered_lines:
    if line == "":
        if not previous_blank:
            compressed_lines.append("")
        previous_blank = True
    else:
        compressed_lines.append(line)
        previous_blank = False

# ==================================================
# STEP 6: MERGE BROKEN SENTENCE LINES
# ==================================================

merged_lines = []
buffer = ""

for line in compressed_lines:
    if line == "":
        if buffer:
            merged_lines.append(buffer.strip())
            buffer = ""
        merged_lines.append("")
        continue

    if not buffer:
        buffer = line
    else:
        if looks_like_sentence_continuation(buffer, line):
            buffer += " " + line
        else:
            merged_lines.append(buffer.strip())
            buffer = line

if buffer:
    merged_lines.append(buffer.strip())

# ==================================================
# STEP 7: FINAL TEXT NORMALIZATION
# ==================================================

clean_text = "\n".join(merged_lines)

clean_text = re.sub(r'[ \t]+', ' ', clean_text)
clean_text = re.sub(r' *\n *', '\n', clean_text)
clean_text = re.sub(r'\n{3,}', '\n\n', clean_text)
clean_text = re.sub(r'\s+([,.;:!?])', r'\1', clean_text)
clean_text = clean_text.strip()

# ==================================================
# SAVE CLEAN TEXT
# ==================================================

os.makedirs(os.path.dirname(output_path), exist_ok=True)

with open(output_path, "w", encoding="utf-8") as f:
    f.write(clean_text)

print("Cleaning complete.")
print(f"Saved to: {output_path}")