import os
import re
import json
from pathlib import Path
from typing import Literal
from dotenv import load_dotenv
from anthropic import Anthropic
from pydantic import BaseModel, ValidationError

# =========================
# LOAD ENV (FIXED)
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
# CLASSIFY BATCH
# =========================

def classify_batch(batch):

    if not batch:
        return []

    numbered = "\n".join([f"{i+1}. {s}" for i, s in enumerate(batch)])

    # 🔥 IMPROVED PROMPT (VERY IMPORTANT)
    prompt = f"""
You are an expert in sustainability reporting analysis.

Classify each sentence into EXACTLY ONE category.

Categories:

1. Future Commitment:
   - Plans, goals, targets, ambitions (future-oriented)

2. Past Achievement:
   - Completed actions or results already achieved

3. Climate Risk Disclosure:
   - Risks, uncertainties, exposure to climate-related issues

4. Quantitative Disclosure:
   - ANY numerical data (%, €, tons, m³, ratios, KPIs, metrics)

5. Symbolic/Vague Language:
   - General statements WITHOUT measurable data
   - Words like "commitment", "approach", "focus", "aim"

6. Regulatory/Framework Reference:
   - Mentions of GRI, TCFD, ESRS, EU taxonomy, GHG Protocol

IMPORTANT RULES:

- If a sentence contains ANY number → it is VERY LIKELY Quantitative
- Quantitative ALWAYS overrides vague language
- Do NOT classify numerical sentences as vague

- Return ONLY JSON list
- Same order as input
- No markdown
- No extra text

Format:
[
  {{"category": "...", "justification": "..."}},
  ...
]

Sentences:
{numbered}
"""

    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=800,
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
            raise ValueError("Mismatch batch size")

        return validated

    except (json.JSONDecodeError, ValidationError, Exception) as e:
        return [
            {
                "category": "ERROR",
                "justification": str(e)
            }
            for _ in batch
        ]