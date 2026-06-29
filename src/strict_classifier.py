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
        "Off-Topic",            # NEW: non-environmental sentences
        "Classification Error", # NEW: genuinely ambiguous sentences
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
# STRICT PROMPT - ONLY THIS SECTION DIFFERS FROM LOOSE
# =========================

def classify_batch(batch: List[str], retry_count: int = 3) -> List[Dict]:
    """
    Classify a batch of sentences with STRICT prompt.
    
    ONLY THE PROMPT IS STRICTER - everything else same as loose classifier.
    """
    
    if not batch:
        return []

    numbered = "\n".join([f"{i+1}. {s}" for i, s in enumerate(batch)])

    # 🔥 STRICT PROMPT - Tighter criteria for Quantitative + Climate Risk
    prompt = f"""You are an expert sustainability analyst detecting greenwashing patterns.

⚠️ STRICT CLASSIFICATION MODE - Reduced Error Margins ⚠️

Classify each sentence into EXACTLY ONE category using these STRICT PRIORITY RULES:

PRIORITY 1 - Regulatory/Framework Reference:
Must include BOTH:
1. Framework name (GRI, TCFD, ESRS, CSRD, Paris Agreement, SBTi, SDG, ISO 14001, 
   EU Taxonomy, GHG Protocol, CDP, VSME)
2. SPECIFIC CONTEXT showing HOW the framework was applied

✓ COUNT (Substantive Use):
- "According to GRI 305-1, our Scope 1 emissions were 50,000 tCO2e"
- "Following TCFD recommendations, we assessed transition risks from carbon pricing"
- "ESRS E1 requires climate adaptation disclosure. Our strategy includes..."
- "Per SBTi methodology, we set 1.5°C-aligned targets reducing emissions 42% by 2030"
- "EU Taxonomy Article 8 screening shows 35% of revenue is taxonomy-aligned"
- "Our report is structured according to TCFD's four pillars: Governance, Strategy, Risk Management, and Metrics"

✗ DO NOT COUNT (Name-Dropping Only):
- "We align with GRI standards"
- "We support the Paris Agreement"
- "TCFD is important to our reporting"
- "Working toward CSRD compliance"
- "This report follows ESRS standards"
- "Sustainability reporting follows international frameworks"

TEST: Does the sentence show the company USED the framework (specific disclosure, 
metric, assessment, reference to specific standard number/article) or just acknowledged 
it exists?

═══════════════════════════════════════════════════════════════════════════
PRIORITY 2 - Quantitative Disclosure (⚠️ STRICT CRITERIA)
═══════════════════════════════════════════════════════════════════════════

🚨 STRICT: Must contain BOTH:
1. ACTUAL DIGITS (0-9)
2. ENVIRONMENTAL/SUSTAINABILITY CONTEXT

Environmental context keywords: emissions, CO2, CO2e, GHG, carbon, renewable, 
energy, water, waste, recycling, circular, sustainability, environmental, 
climate, scope 1, scope 2, scope 3, tCO2, kWh, GWh, reduction, increased, 
decreased, intensity, footprint, temperature, biodiversity, electric, EV, 
BEV, PHEV, electrification

✓ COUNT (Environmental Metrics):
- "Reduced emissions by 40% since 2019"
- "32 million metric tons of CO2e avoided"
- "100% renewable electricity by 2030"
- "Water intensity: 2.16 cubic meters per vehicle"
- "Energy consumption decreased 15%"
- "50,000 tCO2e Scope 1 emissions"
- "Recycling rate increased to 85%"
- "€2.5 billion invested in electrification" (counts - climate investment)
- "17.4% of deliveries were electric vehicles"

✗ DO NOT COUNT (Non-Environmental Numbers):
- "As of January 2025" (just a date) → SYMBOLIC
- "BMW was founded in 1916" (historical date) → SYMBOLIC
- "€20,819 million revenues" (pure financial, not environmental) → SYMBOLIC
- "Rated on a scale of 1 to 4" (rating scale) → SYMBOLIC
- "500 different spare parts available" (inventory count) → SYMBOLIC
- "Launched in 2025" (timeline without environmental metric) → SYMBOLIC
- "Over 15 years ago" (time reference) → SYMBOLIC
- "158,441 employees" (HR data) → SYMBOLIC
- "Period from 2025 to 2030" (timeframe only) → SYMBOLIC

TEST: Does the sentence contain a number ABOUT an environmental/
sustainability metric? If it's just a date, financial figure, or 
non-environmental quantity → NOT quantitative disclosure.

Exception: "€X invested in electrification/renewable energy/sustainability" 
counts as environmental investment.

ALWAYS overrides vague language even if sentence contains aspirational terms.

═══════════════════════════════════════════════════════════════════════════
PRIORITY 3 - Climate Risk Disclosure (⚠️ STRICT CRITERIA)
═══════════════════════════════════════════════════════════════════════════

🚨 STRICT: Must explicitly describe SPECIFIC physical risks OR transition risks 
with CONCRETE DETAILS. NOT just general acknowledgment of climate change.

✓ COUNT (Physical Risks - MUST be specific):
- "Flooding at coastal facilities could disrupt production"
- "Extreme weather impacts on supply chain in Southeast Asia"
- "Rising temperatures affecting manufacturing efficiency"
- "Water scarcity at production sites in drought-prone regions"
- "Hurricanes pose risks to our Gulf Coast operations"
- "Heatwaves may reduce worker productivity at facility X"

✓ COUNT (Transition Risks - MUST be specific):
- "Carbon pricing could increase operational costs by €X per ton"
- "Stricter emissions regulations may require facility retrofits"
- "Technology disruption from EV transition affects ICE vehicle demand"
- "Market shift toward electric vehicles impacts residual values"
- "Reputational risks from stakeholder climate expectations"
- "Policy changes requiring 50% emissions reduction by 2030"
- "Stranded assets from fossil fuel infrastructure"

✗ DO NOT COUNT (General Climate Acknowledgment):
- "Climate change is important" → SYMBOLIC (too general)
- "Climate change poses risks to our business" → SYMBOLIC (too vague - which risks?)
- "We recognize climate challenges" → SYMBOLIC (acknowledgment only)
- "Climate is a priority for our strategy" → SYMBOLIC (no specific risk)
- "We support the Paris Agreement goals" → SYMBOLIC (not a risk statement)
- "Climate change affects operations" → SYMBOLIC (how? where?)
- "We face climate-related risks" → SYMBOLIC (which risks? no details)

TEST: Does the sentence identify a CONCRETE risk with:
1. Risk TYPE (physical: flooding, heat, drought OR transition: policy, market, tech, reputation)
2. What could go wrong (specific impact/consequence)
3. Preferably: where, when, or magnitude

If you cannot identify all three elements → SYMBOLIC, not Climate Risk

═══════════════════════════════════════════════════════════════════════════
PRIORITY 4 - Future Commitment:
Plans, goals, targets, intentions about future actions.
Can have numbers (those go to Quantitative), but if no numbers, classify here.

INDICATORS: will, intend, aim, plan, commit, target, goal, by [future year], 
going to, expect to, working toward

✓ COUNT:
- "We will transition to renewable energy"
- "Our goal is to achieve carbon neutrality"
- "We plan to implement circular economy principles"
- "By 2030 we intend to phase out fossil fuels" (no specific % = Future Commitment)

✗ DO NOT COUNT if has specific numbers:
- "By 2030 we will cut emissions by 50%" → Quantitative Disclosure (has 50%)

PRIORITY 5 - Past Achievement:
Completed actions, documented results, implemented measures.
Can have numbers (those go to Quantitative), but if no numbers, classify here.

INDICATORS: has reduced, achieved, implemented, completed, installed, established, 
since [past year], in [past year], reduced, increased (past tense)

✓ COUNT:
- "We have implemented new environmental policies"
- "Our facilities installed solar panels in 2022"
- "We established a sustainability committee"
- "Energy efficiency measures were completed last year"

✗ DO NOT COUNT if has specific numbers:
- "We reduced emissions by 40% since 2019" → Quantitative Disclosure (has 40%)

PRIORITY 6 - Symbolic/Vague Language:
General environmental statements without data, specifics, or concrete actions.
Use ONLY for sentences that ARE about environmental/sustainability topics
but lack sufficient specificity to qualify for categories 1-5.

INDICATORS: commitment, dedicated, passionate, believe, philosophy, approach, 
focus, values, tradition, culture, spirit, striving, enhancing, promoting, 
supporting (without specifics)

✓ COUNT:
- "We are committed to sustainability"
- "Environmental protection is our priority"
- "We strive for excellence in green manufacturing"
- "Sustainability is at the heart of our strategy"
- "We believe in responsible business practices"
- "Climate change is important" (vague acknowledgment)

TEST: If the sentence IS about environmental/sustainability topics but is too
vague to classify elsewhere → Symbolic/Vague Language.

═══════════════════════════════════════════════════════════════════════════
PRIORITY 7 - Off-Topic:
Sentences with NO environmental or sustainability relevance whatsoever.
Use when the sentence is purely financial, legal, HR, operational, or 
administrative content with no environmental dimension.

✓ COUNT:
- "The Board of Directors met four times in 2024"
- "Revenue increased to €120 billion"
- "We employ 120,000 people worldwide"
- "The company was founded in 1916"
- "Shareholders approved the dividend at the annual meeting"
- "As of January 2025" (date fragment with no environmental context)
- "Page 42 of the Annual Report"

✗ DO NOT COUNT if sentence has ANY environmental dimension → use categories 1-6

═══════════════════════════════════════════════════════════════════════════
PRIORITY 8 - Classification Error:
Use ONLY when the sentence is genuinely impossible to classify because it is
fragmented, corrupted, or so ambiguous that no single category applies.
This should be RARE — fewer than 2% of sentences in a well-extracted report.

✓ COUNT:
- Truncated sentences missing key context
- Sentences mixing multiple unrelated topics equally
- Completely unintelligible text fragments

Do NOT use as a convenience category — attempt classification into 1-7 first.

═══════════════════════════════════════════════════════════════════════════

KEY RULES:
✅ "We reduced emissions by 40%" → Quantitative (has number + environmental)
✅ "By 2030 target 50% reduction" → Quantitative (has number + environmental) 
✅ "We are committed to reducing emissions" → Symbolic/Vague (no number, environmental topic)
✅ "Climate change poses risks" → Symbolic/Vague (too vague)
✅ "Flooding threatens coastal facilities" → Climate Risk (specific + concrete)
✅ "Revenue was €120 billion" → Off-Topic (no environmental dimension)
✅ Corrupted/fragmented text → Classification Error (last resort only)

Return ONLY a JSON array. No markdown, no explanation, no extra text.

Format:
[
  {{"category": "Quantitative Disclosure", "justification": "Environmental metric: 40% emission reduction"}},
  {{"category": "Symbolic/Vague Language", "justification": "Vague environmental commitment without specifics"}},
  {{"category": "Climate Risk Disclosure", "justification": "Concrete physical risk: flooding at coastal facilities"}},
  {{"category": "Off-Topic", "justification": "Pure financial data, no environmental dimension"}},
  {{"category": "Classification Error", "justification": "Fragmented sentence, insufficient context to classify"}},
  ...
]

Sentences to classify:
{numbered}
"""

    for attempt in range(retry_count):
        try:
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=2000,
                temperature=0,
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
                # ✅ FIXED FALLBACK: use Classification Error instead of
                # Symbolic/Vague Language to avoid inflating symbolic counts
                return [
                    {
                        "category": "Classification Error",
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
    
    SAME AS LOOSE CLASSIFIER - only prompt is different.
    """
    
    print(f"\n📄 Reading file: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Split into sentences
    sentences = split_into_sentences(text)
    print(f"✅ Found {len(sentences)} sentences")
    
    # Estimate cost
    estimated_cost = (len(sentences) / batch_size) * 0.003 * 10
    print(f"💰 Estimated API cost: ~${estimated_cost:.2f}")
    
    # Process in batches
    all_results = []
    errors = 0
    
    print(f"\n🔄 Processing in batches of {batch_size}...")
    
    for i in tqdm(range(0, len(sentences), batch_size), desc="Classifying (STRICT)"):
        batch = sentences[i:i + batch_size]
        batch_results = classify_batch(batch)
        
        # Track errors (now Classification Error, not Symbolic)
        for result in batch_results:
            if result["category"] == "Classification Error":
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
    output_file = f"{output_dir}/{company_name}_STRICT_Classification_Results.xlsx"
    
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Detailed Classification', index=False)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"📊 STRICT CLASSIFICATION SUMMARY - {company_name}")
    print(f"{'='*60}")
    print(summary_df.to_string(index=False))
    print(f"\n⚠️  Classification Errors: {errors}")
    print(f"✅ Results saved to: {output_file}")
    print(f"{'='*60}\n")
    
    return output_file

# =========================
# MAIN
# =========================

if __name__ == "__main__":
    filepath = "/mnt/user-data/uploads/BMW_2024_Sustainability_clean.txt"
    output_file = process_file(filepath, batch_size=10)
    
    print(f"✨ Done! Open: {output_file}")