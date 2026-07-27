import json
import pandas as pd
from pathlib import Path
from typing import Dict


def load_classification_results(jsonl_path: Path) -> pd.DataFrame:
    """Load classified sentences from JSONL file."""
    results = []
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            results.append(json.loads(line))
    return pd.DataFrame(results)


def calculate_indicators(df: pd.DataFrame, company_name: str) -> Dict:
    """Calculate all 5 greenwashing indicators and risk score."""

    # ── CHANGE 1: Exclude neutral categories before calculating indicators ──
    # Off-Topic and Classification Error are data quality issues,
    # not greenwashing signals — they must not inflate any category proportion
    EXCLUDED = {'Off-Topic', 'Classification Error'}
    excluded_count = df['category'].isin(EXCLUDED).sum()
    valid_df = df[~df['category'].isin(EXCLUDED)]
    total = len(valid_df)   # <-- use valid sentences only, not len(df)

    if total == 0:
        raise ValueError("No valid sentences remaining after excluding neutral categories.")

    counts = valid_df['category'].value_counts().to_dict()

    # Count each category (from valid sentences only)
    future_count      = counts.get('Future Commitment', 0)
    past_count        = counts.get('Past Achievement', 0)
    symbolic_count    = counts.get('Symbolic/Vague Language', 0)
    quantitative_count= counts.get('Quantitative Disclosure', 0)
    risk_count        = counts.get('Climate Risk Disclosure', 0)
    framework_count   = counts.get('Regulatory/Framework Reference', 0)

    # ── CHANGE 2: Count excluded sentences for reporting transparency ──
    off_topic_count   = df['category'].eq('Off-Topic').sum()
    error_count       = df['category'].eq('Classification Error').sum()

    # Calculate indicators (as proportions of VALID sentences)
    future_to_past_ratio   = future_count / max(past_count, 1)
    symbolic_intensity     = symbolic_count     / total
    quantification_density = quantitative_count / total
    risk_salience          = risk_count         / total
    framework_anchoring    = framework_count    / total

    # ==================================================
    # CALCULATE RISK SCORE (10-POINT SCALE)
    # Each indicator contributes 0-2 points
    # Total possible: 10 points
    # ==================================================

    risk_score = 0
    risk_flags = []

    # 1. Future-to-Past Ratio (0-2 points)
    if future_to_past_ratio > 3.0:
        risk_score += 2
        risk_flags.append("Excessive future commitments (ratio >3.0)")
    elif future_to_past_ratio > 1.0:
        risk_score += 1
        risk_flags.append("Imbalanced commitments (ratio 1.0-3.0)")

    # 2. Symbolic Intensity (0-2 points)
    if symbolic_intensity > 0.50:
        risk_score += 2
        risk_flags.append("Excessive vague language (>50%)")
    elif symbolic_intensity >= 0.30:
        risk_score += 1
        risk_flags.append("Elevated vague language (30-50%)")

    # 3. Quantification Density (0-2 points)
    if quantification_density < 0.30:
        risk_score += 2
        risk_flags.append("Insufficient quantification (<30%)")
    elif quantification_density < 0.60:
        risk_score += 1
        risk_flags.append("Minimal quantification (30-60%)")

    # 4. Risk Salience (0-2 points)
    if risk_salience < 0.10:
        risk_score += 2
        risk_flags.append("Very low risk disclosure (<10%)")
    elif risk_salience <= 0.20:
        risk_score += 1
        risk_flags.append("Low risk disclosure (10-20%)")

    # 5. Framework Anchoring (0-2 points)
    if framework_anchoring < 0.10:
        risk_score += 2
        risk_flags.append("Very low framework integration (<10%)")
    elif framework_anchoring < 0.20:
        risk_score += 1
        risk_flags.append("Low framework integration (10-20%)")

    # Overall risk level
    if risk_score >= 7:
        risk_level = "High Risk"
    elif risk_score >= 4:
        risk_level = "Moderate Risk"
    else:
        risk_level = "Low Risk"

    return {
        'company': company_name,
        'total_sentences_raw': len(df),         # all sentences including excluded
        'total_sentences_valid': total,          # used for indicator calculation
        'excluded_sentences': {                  # ── CHANGE 2: transparency ──
            'Off-Topic': int(off_topic_count),
            'Classification Error': int(error_count),
            'Total excluded': int(excluded_count)
        },
        'category_counts': {
            'Future Commitment': future_count,
            'Past Achievement': past_count,
            'Symbolic/Vague Language': symbolic_count,
            'Quantitative Disclosure': quantitative_count,
            'Climate Risk Disclosure': risk_count,
            'Regulatory/Framework Reference': framework_count
        },
        'indicators': {
            'future_to_past_ratio':   round(future_to_past_ratio, 2),
            'symbolic_intensity':     round(symbolic_intensity, 4),
            'quantification_density': round(quantification_density, 4),
            'risk_salience':          round(risk_salience, 4),
            'framework_anchoring':    round(framework_anchoring, 4)
        },
        'risk_assessment': {
            'score': risk_score,
            'level': risk_level,
            'flags': risk_flags
        }
    }


def save_to_json(indicators: Dict, output_path: Path):
    """Save indicators to JSON file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(indicators, f, indent=2, ensure_ascii=False)


def save_to_excel(indicators: Dict, output_path: Path):
    """Save indicators to formatted Excel file."""

    total_valid = indicators['total_sentences_valid']

    data = {
        'Category': [
            'COMPANY',
            'TOTAL SENTENCES (raw)',
            'TOTAL SENTENCES (valid, used for scoring)',
            'Off-Topic (excluded)',
            'Classification Error (excluded)',
            '',
            'CATEGORIES (% of valid sentences)',
            'Future Commitment',
            'Past Achievement',
            'Symbolic/Vague Language',
            'Quantitative Disclosure',
            'Climate Risk Disclosure',
            'Regulatory/Framework Reference',
            '',
            'INDICATORS',
            'Future-to-Past Ratio',
            'Symbolic Intensity',
            'Quantification Density',
            'Risk Salience',
            'Framework Anchoring',
            '',
            'RISK ASSESSMENT (10-POINT SCALE)',
            'Risk Score',
            'Risk Level',
            'Risk Flags'
        ],
        'Count': [
            indicators['company'],
            indicators['total_sentences_raw'],
            indicators['total_sentences_valid'],
            indicators['excluded_sentences']['Off-Topic'],
            indicators['excluded_sentences']['Classification Error'],
            '',
            '',
            indicators['category_counts']['Future Commitment'],
            indicators['category_counts']['Past Achievement'],
            indicators['category_counts']['Symbolic/Vague Language'],
            indicators['category_counts']['Quantitative Disclosure'],
            indicators['category_counts']['Climate Risk Disclosure'],
            indicators['category_counts']['Regulatory/Framework Reference'],
            '',
            '',
            indicators['indicators']['future_to_past_ratio'],
            indicators['indicators']['symbolic_intensity'],
            indicators['indicators']['quantification_density'],
            indicators['indicators']['risk_salience'],
            indicators['indicators']['framework_anchoring'],
            '',
            '',
            indicators['risk_assessment']['score'],
            indicators['risk_assessment']['level'],
            '; '.join(indicators['risk_assessment']['flags']) if indicators['risk_assessment']['flags'] else 'None'
        ],
        'Percentage': [
            '', '', '', '', '', '', '',
            f"{indicators['category_counts']['Future Commitment']      / total_valid * 100:.1f}%",
            f"{indicators['category_counts']['Past Achievement']       / total_valid * 100:.1f}%",
            f"{indicators['category_counts']['Symbolic/Vague Language']/ total_valid * 100:.1f}%",
            f"{indicators['category_counts']['Quantitative Disclosure']/ total_valid * 100:.1f}%",
            f"{indicators['category_counts']['Climate Risk Disclosure']/ total_valid * 100:.1f}%",
            f"{indicators['category_counts']['Regulatory/Framework Reference'] / total_valid * 100:.1f}%",
            '', '',
            f"{indicators['indicators']['future_to_past_ratio']   * 100:.1f}%",
            f"{indicators['indicators']['symbolic_intensity']      * 100:.1f}%",
            f"{indicators['indicators']['quantification_density']  * 100:.1f}%",
            f"{indicators['indicators']['risk_salience']           * 100:.1f}%",
            f"{indicators['indicators']['framework_anchoring']     * 100:.1f}%",
            '', '',
            f"{indicators['risk_assessment']['score']}/10",
            '', ''
        ]
    }

    df_out = pd.DataFrame(data)
    df_out.to_excel(output_path, index=False, sheet_name='Analysis')


def main():
    """Main execution function."""
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    results_dir = PROJECT_ROOT / "results" / "strict_classifier results"

    # ==================================================
    # CONFIGURATION - CHANGE FOR EACH REPORT
    # ==================================================
    company = "Renault"
    year    = "2020"

    jsonl_file   = results_dir / f"{company}_{year}_strict_classified.jsonl"
    json_output  = results_dir / f"{company}_{year}_strict_indicators.json"
    excel_output = results_dir / f"{company}_{year}_strict_indicators.xlsx"

    if not jsonl_file.exists():
        print(f"❌ Error: Classification file not found: {jsonl_file}")
        return

    print(f"\n{'='*80}")
    print(f"ANALYZING: {company} {year}")
    print(f"{'='*80}\n")

    df = load_classification_results(jsonl_file)
    indicators = calculate_indicators(df, company)

    save_to_json(indicators, json_output)
    save_to_excel(indicators, excel_output)

    print(f"📊 RESULTS:")
    print(f"   Total sentences (raw):   {indicators['total_sentences_raw']}")
    print(f"   Total sentences (valid): {indicators['total_sentences_valid']}")
    print(f"   Off-Topic excluded:      {indicators['excluded_sentences']['Off-Topic']}")
    print(f"   Errors excluded:         {indicators['excluded_sentences']['Classification Error']}")
    print(f"\n📈 INDICATORS (computed on valid sentences):")
    print(f"   Future-to-Past Ratio:    {indicators['indicators']['future_to_past_ratio']}")
    print(f"   Symbolic Intensity:      {indicators['indicators']['symbolic_intensity']:.1%}")
    print(f"   Quantification Density:  {indicators['indicators']['quantification_density']:.1%}")
    print(f"   Risk Salience:           {indicators['indicators']['risk_salience']:.1%}")
    print(f"   Framework Anchoring:     {indicators['indicators']['framework_anchoring']:.1%}")
    print(f"\n⚠️  RISK ASSESSMENT:")
    print(f"   Risk Score: {indicators['risk_assessment']['score']}/10")
    print(f"   Risk Level: {indicators['risk_assessment']['level']}")
    if indicators['risk_assessment']['flags']:
        print(f"   Risk Flags:")
        for flag in indicators['risk_assessment']['flags']:
            print(f"      - {flag}")

    print(f"\n✅ Files saved:")
    print(f"   JSON:  {json_output}")
    print(f"   Excel: {excel_output}")
    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    main()