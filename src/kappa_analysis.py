import pandas as pd
import numpy as np
from sklearn.metrics import cohen_kappa_score, confusion_matrix, classification_report
from pathlib import Path

# =============================================================================
# 0. SETTINGS
# =============================================================================
ANNOTATION_FILE = Path(r"results\validation\kappa_annotation_sample.xlsx")
OUTPUT_FILE     = Path(r"results\validation\kappa_results.xlsx")

CATEGORIES = [
    'Symbolic/Vague Language',
    'Future Commitment',
    'Climate Risk Disclosure',
    'Past Achievement',
    'Regulatory/Framework Reference',
    'Quantitative Disclosure',
]

# =============================================================================
# 1. LOAD DATA
# =============================================================================
df = pd.read_excel(ANNOTATION_FILE, sheet_name='1_Annotate_Here')
df_claude = pd.read_excel(ANNOTATION_FILE, sheet_name='2_Claude_Reference_PRIVATE')

df['Claude_Category'] = df_claude['Claude_Category'].values

print(f"Total sentences: {len(df)}")
print(f"Annotator 1 filled: {df['Annotator_1_Category'].notna().sum()}")
print(f"Annotator 2 filled: {df['Annotator_2_Category'].notna().sum()}")

# =============================================================================
# 2. CLEAN — drop rows where either annotator left blank
# =============================================================================
df_clean = df.dropna(subset=['Annotator_1_Category', 'Annotator_2_Category']).copy()
df_clean = df_clean[
    df_clean['Annotator_1_Category'].isin(CATEGORIES) &
    df_clean['Annotator_2_Category'].isin(CATEGORIES)
].copy()

print(f"Valid rows for analysis: {len(df_clean)}")

# =============================================================================
# 3. HUMAN CONSENSUS LABEL
#    Where A1 and A2 agree → consensus = their shared label
#    Where they disagree → consensus = Annotator 1 (primary coder)
# =============================================================================
df_clean['Consensus'] = np.where(
    df_clean['Annotator_1_Category'] == df_clean['Annotator_2_Category'],
    df_clean['Annotator_1_Category'],
    df_clean['Annotator_1_Category']   # A1 as tie-breaker
)
agreement_rate = (df_clean['Annotator_1_Category'] == df_clean['Annotator_2_Category']).mean()

# =============================================================================
# 4. COHEN'S KAPPA
# =============================================================================
# κ between the two human annotators
kappa_humans = cohen_kappa_score(
    df_clean['Annotator_1_Category'],
    df_clean['Annotator_2_Category']
)

# κ between Claude and human consensus
kappa_claude = cohen_kappa_score(
    df_clean['Consensus'],
    df_clean['Claude_Category']
)

print(f"\n=== COHEN'S KAPPA RESULTS ===")
print(f"κ (Annotator 1 vs Annotator 2):  {kappa_humans:.3f}")
print(f"κ (Claude vs Human Consensus):   {kappa_claude:.3f}")
print(f"Human agreement rate:            {agreement_rate:.1%}")

def interpret_kappa(k):
    if k >= 0.81: return "Almost perfect agreement"
    if k >= 0.61: return "Substantial agreement"
    if k >= 0.41: return "Moderate agreement"
    if k >= 0.21: return "Fair agreement"
    return "Slight agreement"

print(f"\nInterpretation (Landis & Koch 1977):")
print(f"  Human vs Human: {interpret_kappa(kappa_humans)}")
print(f"  Claude vs Human: {interpret_kappa(kappa_claude)}")

# =============================================================================
# 5. CONFUSION MATRIX (Claude vs Human Consensus)
# =============================================================================
cm = confusion_matrix(
    df_clean['Consensus'],
    df_clean['Claude_Category'],
    labels=CATEGORIES
)
cm_df = pd.DataFrame(cm, index=CATEGORIES, columns=CATEGORIES)
cm_df.index.name = 'Human Consensus (ground truth) ↓ / Claude Output →'

print(f"\n=== CONFUSION MATRIX (Claude vs Human Consensus) ===")
print(cm_df)

# =============================================================================
# 6. PER-CATEGORY METRICS
# =============================================================================
report = classification_report(
    df_clean['Consensus'],
    df_clean['Claude_Category'],
    labels=CATEGORIES,
    output_dict=True,
    zero_division=0
)

metrics_rows = []
for cat in CATEGORIES:
    r = report.get(cat, {})
    metrics_rows.append({
        'Category':    cat,
        'Precision':   round(r.get('precision', 0), 3),
        'Recall':      round(r.get('recall', 0), 3),
        'F1_Score':    round(r.get('f1-score', 0), 3),
        'Support (n)': int(r.get('support', 0)),
    })

metrics_df = pd.DataFrame(metrics_rows)
macro_f1 = metrics_df['F1_Score'].mean()
print(f"\n=== PER-CATEGORY METRICS ===")
print(metrics_df.to_string(index=False))
print(f"\nMacro F1: {macro_f1:.3f}")

# =============================================================================
# 7. SAVE RESULTS
# =============================================================================
summary = pd.DataFrame({
    'Metric': [
        'Total sentences annotated',
        'Human agreement rate',
        'κ — Annotator 1 vs Annotator 2',
        'Interpretation (Human vs Human)',
        '',
        'κ — Claude vs Human Consensus',
        'Interpretation (Claude vs Human)',
        'Macro F1 — Claude vs Human',
    ],
    'Value': [
        len(df_clean),
        f"{agreement_rate:.1%}",
        f"{kappa_humans:.3f}",
        interpret_kappa(kappa_humans),
        '',
        f"{kappa_claude:.3f}",
        interpret_kappa(kappa_claude),
        f"{macro_f1:.3f}",
    ]
})

with pd.ExcelWriter(OUTPUT_FILE, engine='openpyxl') as writer:
    summary.to_excel(writer, sheet_name='1_Summary', index=False)
    cm_df.to_excel(writer, sheet_name='2_Confusion_Matrix_Claude_vs_Human')
    metrics_df.to_excel(writer, sheet_name='3_Per_Category_Metrics', index=False)
    df_clean[['Sample_ID', 'Source_Company', 'Source_Year', 'Sentence_Text',
              'Annotator_1_Category', 'Annotator_2_Category',
              'Consensus', 'Claude_Category']].to_excel(
        writer, sheet_name='4_Full_Comparison', index=False)

print(f"\nSaved: {OUTPUT_FILE}")
print("\nDone.")