import pandas as pd
import numpy as np
from pathlib import Path

# =============================================================================
# 0. SETTINGS — update paths to match your folder structure
# =============================================================================
np.random.seed(42)   # fixed seed → reproducible sample

RESULTS_DIR = Path(r"results\strict_classifier results")

# Files to sample from + how many sentences per file
SAMPLE_PLAN = [
    {"file": "BMW_2020_strict_classified.xlsx",   "n": 17},
    {"file": "BMW_2022_strict_classified.xlsx",   "n": 17},
    {"file": "BMW_2024_strict_classified.xlsx",   "n": 16},
    {"file": "Tesla_2020_strict_classified.xlsx", "n": 17},
    {"file": "Tesla_2022_strict_classified.xlsx", "n": 17},
    {"file": "Tesla_2024_strict_classified.xlsx", "n": 16},
    {"file": "BYD_2024_strict_classified.xlsx",   "n": 20},
    # Add more files here if available:
    # {"file": "Peugeot_2024_strict_classified.xlsx", "n": 20},
    # {"file": "Toyota_2024_strict_classified.xlsx",  "n": 20},
]
# Total will be ~120 sentences — adjust n values to reach 150 if more files available

OUTPUT_FILE = Path(r"results\validation\kappa_annotation_sample.xlsx")

VALID_CATEGORIES = [
    'Symbolic/Vague Language',
    'Future Commitment',
    'Climate Risk Disclosure',
    'Past Achievement',
    'Regulatory/Framework Reference',
    'Quantitative Disclosure',
]

# =============================================================================
# 1. SAMPLE SENTENCES FROM EACH FILE
# =============================================================================
all_samples = []
global_id   = 1

for plan in SAMPLE_PLAN:
    filepath = RESULTS_DIR / plan["file"]

    if not filepath.exists():
        print(f"⚠️  File not found, skipping: {filepath}")
        continue

    df = pd.read_excel(filepath)

    # Standardise column names (handle both 'Category' and 'category')
    df.columns = [c.strip() for c in df.columns]
    cat_col  = next((c for c in df.columns if c.lower() == 'category'), None)
    sent_col = next((c for c in df.columns if 'sentence' in c.lower() and 'id' not in c.lower()), None)

    if cat_col is None or sent_col is None:
        print(f"⚠️  Cannot find Category/Sentence columns in {plan['file']}, skipping")
        continue

    # Keep only valid 6-category sentences (exclude Off-Topic, Classification Error)
    valid = df[df[cat_col].isin(VALID_CATEGORIES)].copy()

    # Stratified sample: try to get proportional coverage of all 6 categories
    n_per_cat = max(1, plan["n"] // 6)
    sampled_parts = []
    for cat in VALID_CATEGORIES:
        cat_sentences = valid[valid[cat_col] == cat]
        n_take = min(n_per_cat, len(cat_sentences))
        if n_take > 0:
            sampled_parts.append(cat_sentences.sample(n=n_take, random_state=42))

    sampled = pd.concat(sampled_parts).sample(frac=1, random_state=42)  # shuffle
    sampled = sampled.head(plan["n"])  # cap at requested n

    company = plan["file"].split("_")[0]
    year    = plan["file"].split("_")[1]

    for _, row in sampled.iterrows():
        all_samples.append({
            "Sample_ID":        global_id,
            "Source_Company":   company,
            "Source_Year":      year,
            "Sentence_Text":    str(row[sent_col]).strip(),
            "Claude_Category":  row[cat_col],   # hidden from annotators
        })
        global_id += 1

print(f"Total sentences sampled: {len(all_samples)}")

# =============================================================================
# 2. BUILD ANNOTATION EXCEL
#    Sheet 1: For annotators (NO Claude category visible)
#    Sheet 2: With Claude category (for scoring later — keep private)
#    Sheet 3: Instructions for annotators
# =============================================================================
df_full   = pd.DataFrame(all_samples)

# Annotator view — no Claude_Category column
df_annotator = df_full[["Sample_ID", "Source_Company", "Source_Year", "Sentence_Text"]].copy()
df_annotator["Annotator_1_Category"] = ""   # YOU fill this in
df_annotator["Annotator_2_Category"] = ""   # your annotator fills this in

# Instructions sheet
instructions = pd.DataFrame({
    "INSTRUCTIONS FOR ANNOTATION": [
        "For each sentence, assign ONE category from the list below.",
        "Do NOT look at the other annotator's answers.",
        "Do NOT look at Claude's output (hidden in a separate sheet).",
        "Leave blank only if the sentence is completely unintelligible.",
        "",
        "THE 6 CATEGORIES:",
        "",
        "1. Symbolic/Vague Language",
        "   → General environmental statements WITHOUT data, specifics, or concrete actions",
        "   → Examples: 'We are committed to sustainability'",
        "              'Environmental protection is our priority'",
        "              'We strive for a greener future'",
        "",
        "2. Future Commitment",
        "   → Plans, goals, targets, intentions about FUTURE actions (no specific numbers)",
        "   → Examples: 'We will transition to renewable energy'",
        "              'Our goal is to achieve carbon neutrality'",
        "              'By 2030 we intend to phase out fossil fuels'",
        "",
        "3. Climate Risk Disclosure",
        "   → SPECIFIC physical or transition risks with concrete details",
        "   → Examples: 'Flooding at coastal facilities could disrupt production'",
        "              'Carbon pricing could increase costs by €X per ton'",
        "   → NOT: 'Climate change is important' (too vague → Symbolic)",
        "",
        "4. Past Achievement",
        "   → Completed actions, documented results, implemented measures (no specific numbers)",
        "   → Examples: 'We implemented new environmental policies'",
        "              'Our facilities installed solar panels in 2022'",
        "",
        "5. Regulatory/Framework Reference",
        "   → Explicit reference to GRI, TCFD, CSRD, ESRS, SBTi etc. WITH specific context",
        "   → Examples: 'According to GRI 305-1, our Scope 1 emissions were 50,000 tCO2e'",
        "   → NOT: 'We align with GRI standards' (name-drop only → Symbolic)",
        "",
        "6. Quantitative Disclosure",
        "   → Sentences containing ACTUAL NUMBERS about environmental/sustainability metrics",
        "   → Examples: 'CO2 reduced by 40% since 2019'",
        "              'Renewable energy = 78% of total electricity'",
        "   → NOT: pure financial figures or dates without environmental context",
        "",
        "RULE: If a sentence has a specific number AND an environmental metric → Quantitative",
        "      If vague/general and about environment → Symbolic/Vague",
        "      If it's about something not environmental at all → leave blank (Off-Topic)",
    ]
})

# =============================================================================
# 3. SAVE
# =============================================================================
with pd.ExcelWriter(OUTPUT_FILE, engine='openpyxl') as writer:
    instructions.to_excel(writer, sheet_name='0_READ_FIRST_Instructions', index=False)
    df_annotator.to_excel(writer, sheet_name='1_Annotate_Here', index=False)
    df_full.to_excel(writer, sheet_name='2_Claude_Reference_PRIVATE', index=False)

print(f"\nSaved: {OUTPUT_FILE}")
print("\nNext steps:")
print("  1. Open kappa_annotation_sample.xlsx")
print("  2. Read Sheet '0_READ_FIRST_Instructions'")
print("  3. Fill in 'Annotator_1_Category' column in Sheet '1_Annotate_Here'")
print("  4. Send the SAME file to your second annotator (hide Sheet 2 if needed)")
print("  5. They fill in 'Annotator_2_Category' column")
print("  6. Bring the completed file back → run kappa_analysis.py")