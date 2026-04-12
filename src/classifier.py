import os
import re
import json
from pathlib import Path
from typing import Literal, List, Dict
from dotenv import load_dotenv
from anthropic import Anthropic
from pydantic import BaseModel, ValidationError
import pandas as pd
from tqdm import tqdm

# =========================
# LOAD ENV
# =========================

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    raise ValueError("❌ API key not found. Check your .env file.")

client = Anthropic(api_key=api_key)

# =========================
# SCHEMA
# =========================

class ClassificationResult(BaseModel):
    category: Literal[
        "Future Commitment",
        "Past Achievement",
        "Climate Risk Disclosure",
        "Quantitative Disclosure",
        "Symbolic/Vague Language",
        "Regulatory/Framework Reference",
    ]
    justification: str

# =========================
# IMPROVED: SENTENCE SPLITTING
# =========================

def split_into_sentences(text: str) -> List[str]:
    """Better sentence splitting that preserves context."""
    # Remove excessive whitespace
    text = re.sub(r'\n+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    
    # Split on sentence boundaries
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
    
    # Filter out very short fragments (likely noise)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 15]
    
    return sentences

# =========================
# CLEAN JSON OUTPUT
# =========================

def clean_json_output(raw: str) -> str:
    s = raw.strip()

    # Remove markdown
    s = re.sub(r"^```(?:json)?\s*", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\s*```$", "", s)

    # Extract JSON list
    start = s.find("[")
    end = s.rfind("]")

    if start == -1 or end == -1:
        raise ValueError("No valid JSON found")

    return s[start:end + 1]

# =========================
# IMPROVED: BETTER PROMPT WITH EXAMPLES
# =========================

def classify_batch(batch: List[str], retry_count: int = 3) -> List[Dict]:
    """
    Classify a batch of sentences with improved prompt and retry logic.
    
    IMPROVEMENTS:
    1. Few-shot examples for better accuracy
    2. Explicit prioritization rules
    3. Retry logic for failed classifications
    4. Better error handling
    """
    
    if not batch:
        return []

    numbered = "\n".join([f"{i+1}. {s}" for i, s in enumerate(batch)])

    # 🔥 IMPROVED PROMPT WITH FEW-SHOT EXAMPLES
    prompt = f"""You are an expert sustainability analyst detecting greenwashing patterns.

Classify each sentence into EXACTLY ONE category using these STRICT PRIORITY RULES:

PRIORITY 1 - Regulatory/Framework Reference:
- Mentions GRI, TCFD, ESRS, EU taxonomy, GHG Protocol, Paris Agreement, CSRD, ISO
- Example: "This report follows ESRS standards" → Regulatory/Framework Reference

PRIORITY 2 - Quantitative Disclosure:
- ANY numbers: percentages, currencies, tons, years, ratios, KPIs
- ALWAYS overrides vague language
- Example: "We reduced emissions by 40% since 2019" → Quantitative Disclosure (NOT Past Achievement)
- Example: "By 2030 we will cut CO2 by 50%" → Quantitative Disclosure (NOT Future Commitment)

PRIORITY 3 - Climate Risk Disclosure:
- Discusses risks, uncertainties, challenges, threats, vulnerabilities
- Example: "Climate change poses risks to our supply chain" → Climate Risk Disclosure

PRIORITY 4 - Future Commitment:
- Plans, goals, targets WITHOUT specific numbers
- Words: will, intends, aims, plans, by 2030 (without numbers)
- Example: "We will transition to renewable energy" → Future Commitment

PRIORITY 5 - Past Achievement:
- Completed actions WITHOUT specific numbers
- Words: has reduced, achieved, implemented, completed, since 2015
- Example: "We have implemented new policies" → Past Achievement

PRIORITY 6 - Symbolic/Vague Language:
- General statements without data or specifics
- Words: commitment, approach, focus, belief, philosophy, tradition
- Example: "We are committed to sustainability" → Symbolic/Vague Language

KEY RULES:
✅ "We reduced emissions by 40%" → Quantitative (has number)
✅ "By 2030 target 50% reduction" → Quantitative (has number) 
✅ "We are committed to reducing emissions" → Symbolic/Vague (no number)
✅ "We follow ESRS standards" → Regulatory/Framework
✅ "Climate risks affect operations" → Climate Risk

Return ONLY a JSON array. No markdown, no explanation, no extra text.

Format:
[
  {{"category": "Quantitative Disclosure", "justification": "Contains percentage: 40%"}},
  {{"category": "Symbolic/Vague Language", "justification": "Uses 'committed to' without metrics"}},
  ...
]

Sentences to classify:
{numbered}
"""

    for attempt in range(retry_count):
        try:
            response = client.messages.create(
                model="claude-sonnet-4-6",  # Latest Sonnet
                max_tokens=2000,  # Increased for larger batches
                temperature=0,  # Deterministic
                messages=[{"role": "user", "content": prompt}],
            )

            raw = "".join(
                block.text for block in response.content
                if getattr(block, "type", None) == "text"
            )

            cleaned = clean_json_output(raw)
            parsed = json.loads(cleaned)

            validated = []
            for item in parsed:
                obj = ClassificationResult.model_validate(item).model_dump()
                validated.append(obj)

            # Ensure correct length
            if len(validated) != len(batch):
                raise ValueError(f"Mismatch: got {len(validated)}, expected {len(batch)}")

            return validated

        except (json.JSONDecodeError, ValidationError, ValueError) as e:
            if attempt < retry_count - 1:
                print(f"⚠️  Retry {attempt + 1}/{retry_count} due to: {e}")
                continue
            else:
                # Final fallback
                return [
                    {
                        "category": "Symbolic/Vague Language",
                        "justification": f"Classification failed after {retry_count} attempts: {str(e)}"
                    }
                    for _ in batch
                ]

# =========================
# IMPROVED: MAIN PROCESSING WITH PROGRESS
# =========================

def process_file(filepath: str, batch_size: int = 10, output_dir: str = "/home/claude") -> str:
    """
    Process entire file with batching and progress tracking.
    
    IMPROVEMENTS:
    1. Optimal batch size (10 sentences)
    2. Progress bar
    3. Cost estimation
    4. Excel output with summary
    5. Error tracking
    """
    
    print(f"\n📄 Reading file: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Split into sentences
    sentences = split_into_sentences(text)
    print(f"✅ Found {len(sentences)} sentences")
    
    # Estimate cost
    estimated_cost = (len(sentences) / batch_size) * 0.003 * 10  # Rough estimate
    print(f"💰 Estimated API cost: ~${estimated_cost:.2f}")
    
    # Process in batches
    all_results = []
    errors = 0
    
    print(f"\n🔄 Processing in batches of {batch_size}...")
    
    for i in tqdm(range(0, len(sentences), batch_size), desc="Classifying"):
        batch = sentences[i:i + batch_size]
        batch_results = classify_batch(batch)
        
        # Track errors
        for result in batch_results:
            if "failed" in result["justification"].lower():
                errors += 1
        
        all_results.extend(batch_results)
    
    # Create DataFrame
    df = pd.DataFrame([
        {
            'Sentence_ID': i + 1,
            'Sentence': sentences[i],
            'Category': all_results[i]['category'],
            'Justification': all_results[i]['justification']
        }
        for i in range(len(sentences))
    ])
    
    # Generate summary statistics
    summary = df['Category'].value_counts()
    summary_df = pd.DataFrame({
        'Category': summary.index,
        'Count': summary.values,
        'Percentage': (summary.values / len(df) * 100).round(2)
    })
    
    # Save to Excel
    company_name = Path(filepath).stem.split('_')[0]
    output_file = f"{output_dir}/{company_name}_Classification_Results.xlsx"
    
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Detailed Classification', index=False)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"📊 CLASSIFICATION SUMMARY - {company_name}")
    print(f"{'='*60}")
    print(summary_df.to_string(index=False))
    print(f"\n⚠️  Errors: {errors}")
    print(f"✅ Results saved to: {output_file}")
    print(f"{'='*60}\n")
    
    return output_file

# =========================
# MAIN
# =========================

if __name__ == "__main__":
    # Process BMW file
    filepath = "/mnt/user-data/uploads/BMW_2024_Sustainability_clean.txt"
    output_file = process_file(filepath, batch_size=10)
    
    print(f"✨ Done! Open: {output_file}")