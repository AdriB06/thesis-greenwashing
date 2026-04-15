import os
import re
import pandas as pd
from nltk.tokenize import sent_tokenize

# --------------------------------------------------
# FILE PATHS (EDIT COMPANY / YEAR ONLY HERE)
# --------------------------------------------------

COMPANY = "BMW"
YEAR = 2024

base_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(base_dir)

input_path = os.path.join(
    project_root,
    "data",
    "cleaned_text",
    f"{COMPANY}_{YEAR}_Sustainability_clean.txt"
)

results_sentences_path = os.path.join(
    project_root,
    "results",
    "extracted_sentences"
)

results_metrics_path = os.path.join(
    project_root,
    "results",
    "metrics",
    f"{COMPANY}_{YEAR}_metrics.xlsx"
)

os.makedirs(results_sentences_path, exist_ok=True)
os.makedirs(os.path.join(project_root, "results", "metrics"), exist_ok=True)

# --------------------------------------------------
# LOAD TEXT
# --------------------------------------------------

with open(input_path, "r", encoding="utf-8") as f:
    raw_text = f.read()

# --------------------------------------------------
# CLEAN TEXT (LIGHT CLEANING ONLY)
# --------------------------------------------------

def clean_text(text):
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\b\d{1,3}\b", "", text)  # remove standalone page numbers
    return text

cleaned_text = clean_text(raw_text)
sentences = sent_tokenize(cleaned_text)

# --------------------------------------------------
# KEYWORD DICTIONARIES (HIGH RECALL BUT CLEANER)
# --------------------------------------------------

future_words = [
    "will", "aim", "aims", "intend", "intends",
    "plan", "plans", "target", "targets",
    "transition", "reduce", "achieve"
]

climate_words = [
    "co2", "co2e", "emission", "emissions",
    "carbon", "climate", "scope", "net zero"
]

hedge_words = [
    "may", "might", "could", "approximately",
    "around", "expected", "seek", "anticipate"
]

symbolic_words = [
    "commitment", "ambition", "responsible",
    "vision", "holistic", "strategy",
    "leadership", "pioneer"
]

framework_words = [
    "paris agreement", "sdg", "united nations",
    "esrs", "gri", "sasb", "tcfd",
    "science based target", "sbti",
    "eu taxonomy"
]

past_words = [
    "reduced", "achieved", "decreased",
    "improved", "was reduced",
    "has reduced", "have reduced",
    "was achieved", "were achieved"
]

# REFINED RISK DICTIONARY (NO ESRS BOILERPLATE INFLATION)
risk_words = [
    "physical risk",
    "transition risk",
    "climate risk",
    "climate-related risk",
    "regulatory risk",
    "geopolitical risk",
    "supply chain risk",
    "weather risk",
    "extreme weather",
    "flood",
    "storm",
    "heatwave",
    "drought",
    "damage",
    "asset damage",
    "disruption",
    "shortage",
    "penalty",
    "fine",
    "liability",
    "compliance risk",
    "market risk",
    "carbon price",
    "emissions trading",
    "volatility"
]

# --------------------------------------------------
# STORAGE
# --------------------------------------------------

future_climate = []
hedge_sentences = []
symbolic_sentences = []
number_sentences = []
framework_sentences = []
past_sentences = []
risk_sentences = []

# --------------------------------------------------
# CLASSIFICATION LOOP
# --------------------------------------------------

for sentence in sentences:

    s = sentence.lower()

    if len(s.split()) < 8:
        continue

    # Skip structural ESRS boilerplate lines
    if "material impacts, risks and opportunities" in s:
        continue

    # FUTURE + CLIMATE
    if any(f in s for f in future_words) and any(c in s for c in climate_words):
        future_climate.append(sentence)

    # HEDGE
    if any(h in s for h in hedge_words):
        hedge_sentences.append(sentence)

    # SYMBOLIC
    if any(sym in s for sym in symbolic_words):
        symbolic_sentences.append(sentence)

    # NUMERIC
    if re.search(r"\d", s):
        number_sentences.append(sentence)

    # FRAMEWORK REFERENCES
    if any(fr in s for fr in framework_words):
        framework_sentences.append(sentence)

    # PAST ACHIEVEMENT (CLIMATE RELATED)
    if any(p in s for p in past_words) and any(c in s for c in climate_words):
        past_sentences.append(sentence)

    # RISK EXPOSURE (CLIMATE CONTEXT)
    if any(r in s for r in risk_words) and any(c in s for c in climate_words):
        risk_sentences.append(sentence)

# --------------------------------------------------
# SAVE SENTENCES
# --------------------------------------------------

def save_file(filename, data):
    path = os.path.join(results_sentences_path, filename)
    with open(path, "w", encoding="utf-8") as f:
        for line in data:
            f.write(line.strip() + "\n\n")

save_file("Future_Climate_Sentences.txt", future_climate)
save_file("Hedge_Sentences.txt", hedge_sentences)
save_file("Symbolic_Sentences.txt", symbolic_sentences)
save_file("Number_Sentences.txt", number_sentences)
save_file("Framework_Reference_Sentences.txt", framework_sentences)
save_file("Past_Achievement_Sentences.txt", past_sentences)
save_file("Risk_Exposure_Sentences.txt", risk_sentences)

# --------------------------------------------------
# EXPORT METRICS (RAW COUNTS ONLY)
# --------------------------------------------------

metrics = {
    "Company": [COMPANY],
    "Year": [YEAR],
    "Future_Climate_Sentences": [len(future_climate)],
    "Past_Achievement_Sentences": [len(past_sentences)],
    "Hedge_Sentences": [len(hedge_sentences)],
    "Symbolic_Sentences": [len(symbolic_sentences)],
    "Number_Sentences": [len(number_sentences)],
    "Framework_Reference_Sentences": [len(framework_sentences)],
    "Risk_Exposure_Sentences": [len(risk_sentences)],
}

df = pd.DataFrame(metrics)
df.to_excel(results_metrics_path, index=False)

print("Extraction complete.")