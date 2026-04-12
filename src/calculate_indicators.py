import json
import csv
import os
from collections import Counter

# =========================
# FILE PATHS
# =========================

INPUT_FILE = "results/bmw_2024_results.json"

OUTPUT_SENTENCES_CSV = "results/bmw_2024_sentences.csv"
OUTPUT_INDICATORS_JSON = "results/bmw_2024_indicators.json"
OUTPUT_INDICATORS_CSV = "results/bmw_2024_indicators.csv"


# =========================
# SAFE FILE REMOVE (fix permission issues)
# =========================

def safe_remove(file_path):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except PermissionError:
        print(f"⚠️ Could not overwrite {file_path} (probably open in Excel)")
        print("👉 Close the file and run again.")
        exit()


# Remove old files safely
safe_remove(OUTPUT_SENTENCES_CSV)
safe_remove(OUTPUT_INDICATORS_CSV)
safe_remove(OUTPUT_INDICATORS_JSON)


# =========================
# LOAD DATA
# =========================

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

# Remove errors safely
data = [item for item in data if item.get("category") != "ERROR"]

if len(data) == 0:
    print("❌ No valid data found. Check classification output.")
    exit()

print(f"Loaded {len(data)} classified sentences.")


# =========================
# EXPORT SENTENCE DATASET
# =========================

with open(OUTPUT_SENTENCES_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f, delimiter=";")

    # Clean headers (capitalized)
    writer.writerow(["ID", "Sentence", "Category", "Justification"])

    for i, item in enumerate(data):
        writer.writerow([
            i + 1,
            item.get("sentence", ""),
            item.get("category", ""),
            item.get("justification", "")
        ])

print(f"✅ Sentence dataset saved: {OUTPUT_SENTENCES_CSV}")


# =========================
# CALCULATE INDICATORS
# =========================

categories = [item.get("category") for item in data]
counts = Counter(categories)

total = len(categories)

future = counts.get("Future Commitment", 0)
past = counts.get("Past Achievement", 0)
risk = counts.get("Climate Risk Disclosure", 0)
quant = counts.get("Quantitative Disclosure", 0)
symbolic = counts.get("Symbolic/Vague Language", 0)
framework = counts.get("Regulatory/Framework Reference", 0)


def safe_div(n, d):
    return round(n / d, 4) if d != 0 else 0.0


indicators = {
    "Total Sentences": total,

    "Future Commitment Count": future,
    "Past Achievement Count": past,
    "Climate Risk Disclosure Count": risk,
    "Quantitative Disclosure Count": quant,
    "Symbolic/Vague Language Count": symbolic,
    "Regulatory/Framework Reference Count": framework,

    # Ratios
    "Symbolic Intensity Ratio": safe_div(symbolic, total),
    "Quantification Density": safe_div(quant, total),
    "Risk Salience Ratio": safe_div(risk, total),
    "Framework Anchoring Ratio": safe_div(framework, total),

    # Balance
    "Future Orientation Ratio": safe_div(future, future + past),
    "Past Orientation Ratio": safe_div(past, future + past),
}


# =========================
# SAVE INDICATORS (JSON)
# =========================

with open(OUTPUT_INDICATORS_JSON, "w", encoding="utf-8") as f:
    json.dump(indicators, f, indent=2, ensure_ascii=False)

print(f"✅ Indicators saved (JSON): {OUTPUT_INDICATORS_JSON}")


# =========================
# SAVE INDICATORS (CSV)
# =========================

with open(OUTPUT_INDICATORS_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f, delimiter=";")

    writer.writerow(["Indicator", "Value"])

    for key, value in indicators.items():
        writer.writerow([key, value])

print(f"✅ Indicators saved (CSV): {OUTPUT_INDICATORS_CSV}")


# =========================
# DONE
# =========================

print("\n🎯 All outputs successfully generated!")