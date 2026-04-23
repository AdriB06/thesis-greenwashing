import json
import pandas as pd
from pathlib import Path
from typing import Dict


def load_classification_results(jsonl_path: Path) -> pd.DataFrame:
    results = []
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            results.append(json.loads(line))
    return pd.DataFrame(results)


def calculate_indicators(df: pd.DataFrame, company_name: str) -> Dict:
    counts = df['category'].value_counts().to_dict()
    total = len(df)
    
    future_count = counts.get('Future Commitment', 0)
    past_count = counts.get('Past Achievement', 0)
    symbolic_count = counts.get('Symbolic/Vague Language', 0)
    quantitative_count = counts.get('Quantitative Disclosure', 0)
    risk_count = counts.get('Climate Risk Disclosure', 0)
    framework_count = counts.get('Regulatory/Framework Reference', 0)
    
    future_to_past_ratio = future_count / max(past_count, 1)
    symbolic_intensity = symbolic_count / total
    quantification_density = quantitative_count / total
    risk_salience = risk_count / total
    framework_anchoring = framework_count / total
    
    risk_score = 0
    risk_flags = []
    
    if future_to_past_ratio > 5:
        risk_score += 2
        risk_flags.append("High Future-to-Past ratio (>5)")
    elif future_to_past_ratio > 3:
        risk_score += 1
        risk_flags.append("Moderate Future-to-Past ratio (3-5)")
    
    if symbolic_intensity > 0.40:
        risk_score += 2
        risk_flags.append("High vague language (>40%)")
    elif symbolic_intensity > 0.30:
        risk_score += 1
        risk_flags.append("Moderate vague language (30-40%)")
    
    if quantification_density < 0.15:
        risk_score += 2
        risk_flags.append("Low quantification (<15%)")
    elif quantification_density < 0.25:
        risk_score += 1
        risk_flags.append("Moderate quantification (15-25%)")
    
    if risk_score >= 5:
        risk_level = "High Risk"
    elif risk_score >= 3:
        risk_level = "Moderate Risk"
    else:
        risk_level = "Low Risk"
    
    return {
        'company': company_name,
        'total_sentences': total,
        'category_counts': {
            'Future Commitment': future_count,
            'Past Achievement': past_count,
            'Symbolic/Vague Language': symbolic_count,
            'Quantitative Disclosure': quantitative_count,
            'Climate Risk Disclosure': risk_count,
            'Regulatory/Framework Reference': framework_count
        },
        'indicators': {
            'future_to_past_ratio': round(future_to_past_ratio, 2),
            'symbolic_intensity': round(symbolic_intensity, 4),
            'quantification_density': round(quantification_density, 4),
            'risk_salience': round(risk_salience, 4),
            'framework_anchoring': round(framework_anchoring, 4)
        },
        'risk_assessment': {
            'score': risk_score,
            'level': risk_level,
            'flags': risk_flags
        }
    }


def save_to_json(indicators: Dict, output_path: Path):
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(indicators, f, indent=2, ensure_ascii=False)


def save_to_excel(indicators: Dict, output_path: Path):
    data = {
        'Category': [
            'COMPANY',
            'TOTAL SENTENCES',
            '',
            'CATEGORIES',
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
            'RISK ASSESSMENT',
            'Risk Score',
            'Risk Level',
            'Risk Flags'
        ],
        'Count': [
            indicators['company'],
            indicators['total_sentences'],
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
            '',
            '',
            '',
            '',
            f"{indicators['category_counts']['Future Commitment']/indicators['total_sentences']*100:.1f}%",
            f"{indicators['category_counts']['Past Achievement']/indicators['total_sentences']*100:.1f}%",
            f"{indicators['category_counts']['Symbolic/Vague Language']/indicators['total_sentences']*100:.1f}%",
            f"{indicators['category_counts']['Quantitative Disclosure']/indicators['total_sentences']*100:.1f}%",
            f"{indicators['category_counts']['Climate Risk Disclosure']/indicators['total_sentences']*100:.1f}%",
            f"{indicators['category_counts']['Regulatory/Framework Reference']/indicators['total_sentences']*100:.1f}%",
            '',
            '',
            f"{indicators['indicators']['future_to_past_ratio']*100:.1f}%",
            f"{indicators['indicators']['symbolic_intensity']*100:.1f}%",
            f"{indicators['indicators']['quantification_density']*100:.1f}%",
            f"{indicators['indicators']['risk_salience']*100:.1f}%",
            f"{indicators['indicators']['framework_anchoring']*100:.1f}%",
            '',
            '',
            f"{indicators['risk_assessment']['score']}/6",
            '',
            ''
        ]
    }
    
    df = pd.DataFrame(data)
    df.to_excel(output_path, index=False, sheet_name='Analysis')


def main():
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    results_dir = PROJECT_ROOT / "results"
    
    company = "BMW"
    
    jsonl_file = results_dir / f"{company}_2022_classified.jsonl"
    json_output = results_dir / f"{company}_2022_indicators.json"
    excel_output = results_dir / f"{company}_2022_indicators.xlsx"
    
    if not jsonl_file.exists():
        print(f"❌ Error: Classification file not found: {jsonl_file}")
        return
    
    print(f"🔍 Analyzing: {company} 2022")
    
    df = load_classification_results(jsonl_file)
    indicators = calculate_indicators(df, company)
    
    save_to_json(indicators, json_output)
    save_to_excel(indicators, excel_output)
    
    print(f"✅ JSON: {json_output.name}")
    print(f"✅ Excel: {excel_output.name}")
    print(f"📊 {indicators['risk_assessment']['level']}")


if __name__ == "__main__":
    main()