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
    "Tesla_2022_Sustainability_raw.txt"
)

output_path = os.path.join(
    project_root,
    "data",
    "cleaned_text",
    "Tesla_2022_Sustainability_clean.txt"
)

# ==================================================
# LOAD RAW TEXT
# ==================================================

with open(input_path, "r", encoding="utf-8") as f:
    text = f.read()

# ==================================================
# STEP 1: NORMALIZE PDF ARTIFACTS
# ==================================================

# Convert form feed/page break to newline
text = text.replace("\x0c", "\n")

# Remove arrow symbols often produced by PDF extraction
text = text.replace("↗", " ")

# Fix common weird spaces
text = text.replace("\u00a0", " ")
text = text.replace("\u2009", " ")
text = text.replace("\u202f", " ")

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
    "Tesla Impact Report",
    "2022 Tesla Impact Report",
    "Table of Contents",
]

CONTENTS_HINTS = [
    "Master Plan",
    "Mission",
    "Strategy",
    "Environmental Impact",
    "Product",
    "Electric Vehicles",
    "Charging",
    "EVs",
    "Grid",
    "Energy Storage",
    "Supply Chain",
    "Governance",
    "Climate",
    "TCFD",
    "Appendix",
    "SASB",
    "Metrics",
]

def is_page_number(line: str) -> bool:
    return bool(re.fullmatch(r"\d{1,3}", line.strip()))

def is_report_header(line: str) -> bool:
    stripped = line.strip()
    return any(h in stripped for h in HEADER_PATTERNS)

def is_spaced_caps(line: str) -> bool:
    # Example: "H O L I S T I C   E N V I R O N M E N T A L ..."
    return bool(re.fullmatch(r'(?:[A-Z]\s+){5,}[A-Z]', line.strip()))

def is_all_caps_title(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False

    letters = re.sub(r'[^A-Za-z]', '', stripped)
    if len(letters) < 6:
        return False

    uppercase_ratio = sum(1 for c in letters if c.isupper()) / len(letters)

    # Remove likely section titles, but do not remove short metric labels too aggressively
    return uppercase_ratio > 0.9 and len(stripped) < 140 and len(stripped.split()) >= 3

def is_contents_entry(line: str) -> bool:
    stripped = line.strip()

    # Lines like "95 General Basis for Preparation..."
    if re.match(r'^\d{1,3}\s+[A-Z]', stripped):
        return True

    # Lines with only section-name style content from contents pages
    if any(hint in stripped for hint in CONTENTS_HINTS):
        # Protect real prose sentences by requiring no final punctuation
        if not re.search(r'[.!?]$', stripped):
            return True

    return False

def is_table_noise(line: str) -> bool:
    stripped = line.strip()

    # Very short label-only fragments often coming from tables/graphics
    if len(stripped) <= 3:
        return True

    # Repeated filler artifacts
    if stripped.lower().startswith("dummy "):
        return True

    # Mostly symbols/numbers
    if re.fullmatch(r'[\d\s\-–—./,%()]+', stripped):
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

    # If next starts lowercase, it likely continues
    if re.match(r'^[a-z]', nxt):
        return True

    # If previous ends with comma or open bracket, likely continues
    if re.search(r'[,\(\-]$', prev):
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
# Keep paragraph boundaries, but merge PDF-wrapped lines
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

# Clean spaces, but preserve line breaks
clean_text = re.sub(r'[ \t]+', ' ', clean_text)
clean_text = re.sub(r' *\n *', '\n', clean_text)
clean_text = re.sub(r'\n{3,}', '\n\n', clean_text)

# Remove awkward spaces before punctuation
clean_text = re.sub(r'\s+([,.;:!?])', r'\1', clean_text)

# Final trim
clean_text = clean_text.strip()

# ==================================================
# SAVE CLEAN TEXT
# ==================================================

with open(output_path, "w", encoding="utf-8") as f:
    f.write(clean_text)

print("Cleaning complete.")
print(f"Saved to: {output_path}")
