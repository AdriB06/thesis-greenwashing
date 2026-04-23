import os
import json
from pathlib import Path
from classifier import classify_batch, split_into_sentences
import pandas as pd
from tqdm import tqdm

# =========================
# CONFIG
# =========================

BATCH_SIZE = 10

# =========================
# PATHS (UPDATED FOR NEW STRUCTURE)
# =========================

# Get project root (thesis-greenwashing folder)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Input/Output paths
input_path = PROJECT_ROOT / "data" / "cleaned_text" / "BMW_2022_Sustainability_clean.txt"
output_dir = PROJECT_ROOT / "results"
output_jsonl = output_dir / "BMW_2022_classified.jsonl"
output_excel = output_dir / "BMW_2022_classified.xlsx"

# =========================
# CREATE RESULTS FOLDER
# =========================

output_dir.mkdir(exist_ok=True)

# =========================
# LOAD TEXT & SPLIT SENTENCES
# =========================

print(f"\n📄 Reading: {input_path}")

with open(input_path, "r", encoding="utf-8") as f:
    text = f.read()

# Use improved sentence splitting from classifier
sentences = split_into_sentences(text)

print(f"✅ Total sentences: {len(sentences)}")

# =========================
# ESTIMATE COST
# =========================

num_batches = (len(sentences) + BATCH_SIZE - 1) // BATCH_SIZE
estimated_cost = num_batches * 0.003 * 10

print(f"💰 Estimated API cost: ~${estimated_cost:.2f}")

# =========================
# RESUME SUPPORT
# =========================

processed = 0
all_results = []

if output_jsonl.exists():
    with open(output_jsonl, "r", encoding="utf-8") as f:
        for line in f:
            all_results.append(json.loads(line))
    processed = len(all_results)
    print(f"🔄 Resuming from sentence: {processed}")

# =========================
# RUN PIPELINE
# =========================

errors = 0

if processed < len(sentences):
    print(f"\n🚀 Starting classification...")
    
    with open(output_jsonl, "a", encoding="utf-8") as f:
        
        for i in tqdm(range(processed, len(sentences), BATCH_SIZE), desc="Classifying"):
            batch = sentences[i:i + BATCH_SIZE]
            
            try:
                results = classify_batch(batch, retry_count=3)
                
                # Save to JSONL
                for sentence, result in zip(batch, results):
                    entry = {
                        "sentence": sentence,
                        "category": result["category"],
                        "justification": result["justification"]
                    }
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                    all_results.append(entry)
                
                # Track errors
                for result in results:
                    if "failed" in result["justification"].lower():
                        errors += 1
                        
            except Exception as e:
                print(f"\n⚠️  Error at batch {i}: {e}")
                errors += BATCH_SIZE
                continue

print(f"\n✅ Classification complete!")

# =========================
# GENERATE EXCEL OUTPUT
# =========================

print(f"\n📊 Generating Excel report...")

# Create DataFrame
df = pd.DataFrame([
    {
        'Sentence_ID': i + 1,
        'Sentence': result['sentence'],
        'Category': result['category'],
        'Justification': result['justification']
    }
    for i, result in enumerate(all_results)
])

# Generate summary
summary = df['Category'].value_counts()
summary_df = pd.DataFrame({
    'Category': summary.index,
    'Count': summary.values,
    'Percentage': (summary.values / len(df) * 100).round(2)
})

# Save to Excel
with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
    df.to_excel(writer, sheet_name='Detailed Classification', index=False)
    summary_df.to_excel(writer, sheet_name='Summary', index=False)

# =========================
# PRINT SUMMARY
# =========================

print(f"\n{'='*60}")
print(f"📊 CLASSIFICATION SUMMARY - BMW 2022")
print(f"{'='*60}")
print(summary_df.to_string(index=False))
print(f"\n⚠️  Total errors: {errors}")
print(f"✅ Success rate: {((len(sentences) - errors) / len(sentences) * 100):.1f}%")
print(f"\n📁 Results saved to:")
print(f"   • JSONL: {output_jsonl}")
print(f"   • Excel: {output_excel}")
print(f"{'='*60}\n")