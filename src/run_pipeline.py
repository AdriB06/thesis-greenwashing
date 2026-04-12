import os
import re
import json
from classifier import classify_batch

# =========================
# CONFIG
# =========================

BATCH_SIZE = 10

# =========================
# PATHS
# =========================

base_dir = os.path.dirname(os.path.abspath(__file__))  # llm_method
project_root = os.path.dirname(base_dir)

input_path = os.path.join(
    project_root,
    "data",
    "cleaned_text",
    "BMW_2024_Sustainability_clean.txt"
)

output_path = os.path.join(
    base_dir,
    "results",
    "BMW_2024_classified.jsonl"
)

# =========================
# CREATE RESULTS FOLDER
# =========================

os.makedirs(os.path.dirname(output_path), exist_ok=True)

# =========================
# LOAD TEXT
# =========================

with open(input_path, "r", encoding="utf-8") as f:
    text = f.read()

# =========================
# SPLIT INTO SENTENCES
# =========================

sentences = re.split(r'(?<=[.!?])\s+', text)

# Basic filtering
sentences = [s.strip() for s in sentences if len(s.strip()) > 40]

print(f"Total sentences: {len(sentences)}")

# =========================
# RESUME SUPPORT
# =========================

processed = 0

if os.path.exists(output_path):
    with open(output_path, "r", encoding="utf-8") as f:
        processed = sum(1 for _ in f)

print(f"Resuming from: {processed}")

# =========================
# RUN PIPELINE
# =========================

with open(output_path, "a", encoding="utf-8") as f:

    for i in range(processed, len(sentences), BATCH_SIZE):

        batch = sentences[i:i + BATCH_SIZE]
        results = classify_batch(batch)

        for sentence, result in zip(batch, results):

            entry = {
                "sentence": sentence,
                "category": result["category"],
                "justification": result["justification"]
            }

            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        print(f"Processed: {i + len(batch)} / {len(sentences)}")

print("✅ Pipeline complete.")