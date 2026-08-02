import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc
import seaborn as sns
from pathlib import Path

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 10)

# =========================
# CONFIGURATION
# =========================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "results" / "validation" / "classifier_selection"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Input files (classified sentences)
BMW_LOOSE_CLASSIFIED = PROJECT_ROOT / "results" / "loose_classifier results" / "BMW_2014_loose_classified.xlsx"
BMW_STRICT_CLASSIFIED = PROJECT_ROOT / "results" / "strict_classifier results" / "BMW_2014_strict_classified.xlsx"
VW_LOOSE_CLASSIFIED = PROJECT_ROOT / "results" / "loose_classifier results" / "VW_2014_loose_classified.xlsx"
VW_STRICT_CLASSIFIED = PROJECT_ROOT / "results" / "strict_classifier results" / "VW_2014_strict_classified.xlsx"

# =========================
# RISK SCORING SYSTEM
# =========================

# Each category gets a "greenwashing risk score" (0-1 scale)
CATEGORY_RISK_SCORES = {
    'Quantitative Disclosure': 0.1,        # Low risk: concrete, verifiable data
    'Regulatory/Framework Reference': 0.15,# Low risk: external anchoring
    'Past Achievement': 0.2,               # Low risk: evidence-based claims
    'Climate Risk Disclosure': 0.3,        # Medium-low: transparency signal
    'Future Commitment': 0.5,              # Medium risk: promises without evidence
    'Symbolic/Vague Language': 0.9         # High risk: greenwashing signal
}

# =========================
# FUNCTIONS
# =========================

def load_and_score_sentences(classified_file, label_name):
    """
    Load classified sentences and assign risk scores.
    
    Args:
        classified_file: Path to Excel file with classified sentences
        label_name: Name for this dataset (e.g., "BMW 2014" or "VW 2014")
    
    Returns:
        DataFrame with Sentence, Category, Risk_Score, True_Label columns
    """
    df = pd.read_excel(classified_file)
    
    # Assign risk scores based on category
    df['Risk_Score'] = df['Category'].map(CATEGORY_RISK_SCORES)
    
    # Assign true label (0 = quality/BMW, 1 = greenwashing/VW)
    df['True_Label'] = 1 if 'VW' in label_name else 0
    df['Report'] = label_name
    
    return df[['Sentence', 'Category', 'Risk_Score', 'True_Label', 'Report']]

def calculate_auc_metrics(y_true, y_scores):
    """
    Calculate ROC curve and AUC.
    
    Args:
        y_true: True labels (0=quality, 1=greenwashing)
        y_scores: Predicted risk scores (0-1)
    
    Returns:
        dict with fpr, tpr, auc, and optimal_threshold
    """
    fpr, tpr, thresholds = roc_curve(y_true, y_scores)
    roc_auc = auc(fpr, tpr)
    
    # Find optimal threshold (maximize Youden's J statistic)
    j_scores = tpr - fpr
    optimal_idx = np.argmax(j_scores)
    optimal_threshold = thresholds[optimal_idx]
    
    return {
        'fpr': fpr,
        'tpr': tpr,
        'auc': roc_auc,
        'optimal_threshold': optimal_threshold,
        'optimal_tpr': tpr[optimal_idx],
        'optimal_fpr': fpr[optimal_idx]
    }

def interpret_auc(auc_value):
    """Interpret AUC value."""
    if auc_value >= 0.9:
        return "Excellent"
    elif auc_value >= 0.8:
        return "Good"
    elif auc_value >= 0.7:
        return "Acceptable"
    elif auc_value >= 0.6:
        return "Poor"
    else:
        return "Failed (worse than random)"

# =========================
# MAIN ANALYSIS
# =========================

def main():
    print("="*80)
    print("SENTENCE-LEVEL AUC ANALYSIS")
    print("="*80)
    print("\nQuestion: How well does each classifier rank quality sentences")
    print("          (BMW 2014) as lower risk than greenwashing sentences (VW 2014)?")
    print("\nMeasure: AUC (Area Under ROC Curve)")
    print("  • AUC = 0.5: Random (no discrimination)")
    print("  • AUC = 0.7: Acceptable discrimination")
    print("  • AUC = 0.9: Excellent discrimination\n")
    
    # =========================
    # LOAD DATA
    # =========================
    
    print("="*80)
    print("LOADING DATA")
    print("="*80 + "\n")
    
    # Load loose classifier data
    bmw_loose = load_and_score_sentences(BMW_LOOSE_CLASSIFIED, "BMW 2014")
    vw_loose = load_and_score_sentences(VW_LOOSE_CLASSIFIED, "VW 2014")
    loose_data = pd.concat([bmw_loose, vw_loose], ignore_index=True)
    
    print(f"Loose Classifier:")
    print(f"  BMW 2014: {len(bmw_loose)} sentences")
    print(f"  VW 2014:  {len(vw_loose)} sentences")
    print(f"  Total:    {len(loose_data)} sentences\n")
    
    # Load strict classifier data
    bmw_strict = load_and_score_sentences(BMW_STRICT_CLASSIFIED, "BMW 2014")
    vw_strict = load_and_score_sentences(VW_STRICT_CLASSIFIED, "VW 2014")
    strict_data = pd.concat([bmw_strict, vw_strict], ignore_index=True)
    
    print(f"Strict Classifier:")
    print(f"  BMW 2014: {len(bmw_strict)} sentences")
    print(f"  VW 2014:  {len(vw_strict)} sentences")
    print(f"  Total:    {len(strict_data)} sentences\n")
    
    # =========================
    # CALCULATE AUC
    # =========================
    
    print("="*80)
    print("AUC CALCULATION")
    print("="*80 + "\n")
    
    # Loose classifier AUC
    loose_metrics = calculate_auc_metrics(
        loose_data['True_Label'].values,
        loose_data['Risk_Score'].values
    )
    
    print(f"LOOSE CLASSIFIER:")
    print(f"  AUC: {loose_metrics['auc']:.4f} ({interpret_auc(loose_metrics['auc'])})")
    print(f"  Optimal Threshold: {loose_metrics['optimal_threshold']:.3f}")
    print(f"  At optimal: TPR={loose_metrics['optimal_tpr']:.3f}, FPR={loose_metrics['optimal_fpr']:.3f}")
    
    # Strict classifier AUC
    strict_metrics = calculate_auc_metrics(
        strict_data['True_Label'].values,
        strict_data['Risk_Score'].values
    )
    
    print(f"\nSTRICT CLASSIFIER:")
    print(f"  AUC: {strict_metrics['auc']:.4f} ({interpret_auc(strict_metrics['auc'])})")
    print(f"  Optimal Threshold: {strict_metrics['optimal_threshold']:.3f}")
    print(f"  At optimal: TPR={strict_metrics['optimal_tpr']:.3f}, FPR={strict_metrics['optimal_fpr']:.3f}")
    
    # =========================
    # COMPARISON
    # =========================
    
    print("\n" + "="*80)
    print("CLASSIFIER COMPARISON")
    print("="*80 + "\n")
    
    auc_diff = strict_metrics['auc'] - loose_metrics['auc']
    auc_ratio = strict_metrics['auc'] / loose_metrics['auc']
    
    if auc_diff > 0.05:
        winner = "STRICT"
        advantage = auc_ratio
    elif auc_diff < -0.05:
        winner = "LOOSE"
        advantage = 1 / auc_ratio
    else:
        winner = "TIE"
        advantage = 1.0
    
    print(f"AUC Difference: {auc_diff:+.4f}")
    print(f"AUC Ratio: {auc_ratio:.2f}x")
    
    if winner == "TIE":
        print(f"\n⚖️  RESULT: Tie (difference < 0.05)")
        print(f"   Both classifiers have similar discrimination ability")
    else:
        print(f"\n🏆 WINNER: {winner} CLASSIFIER")
        print(f"   Better discrimination by {abs(auc_diff):.4f} AUC points")
    
    # =========================
    # DISTRIBUTION ANALYSIS
    # =========================
    
    print("\n" + "="*80)
    print("RISK SCORE DISTRIBUTIONS")
    print("="*80 + "\n")
    
    print("LOOSE CLASSIFIER:")
    print(f"  BMW mean score: {bmw_loose['Risk_Score'].mean():.3f} (±{bmw_loose['Risk_Score'].std():.3f})")
    print(f"  VW mean score:  {vw_loose['Risk_Score'].mean():.3f} (±{vw_loose['Risk_Score'].std():.3f})")
    print(f"  Separation: {vw_loose['Risk_Score'].mean() - bmw_loose['Risk_Score'].mean():.3f}")
    
    print(f"\nSTRICT CLASSIFIER:")
    print(f"  BMW mean score: {bmw_strict['Risk_Score'].mean():.3f} (±{bmw_strict['Risk_Score'].std():.3f})")
    print(f"  VW mean score:  {vw_strict['Risk_Score'].mean():.3f} (±{vw_strict['Risk_Score'].std():.3f})")
    print(f"  Separation: {vw_strict['Risk_Score'].mean() - bmw_strict['Risk_Score'].mean():.3f}")
    
    # =========================
    # VISUALIZATION
    # =========================
    
    print("\n" + "="*80)
    print("GENERATING VISUALIZATIONS")
    print("="*80 + "\n")
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Sentence-Level AUC Analysis: Ranking Quality vs Greenwashing', 
                 fontsize=16, fontweight='bold')
    
    # 1. ROC Curves Comparison
    ax = axes[0, 0]
    ax.plot(loose_metrics['fpr'], loose_metrics['tpr'], 'b-', lw=2,
            label=f"Loose (AUC = {loose_metrics['auc']:.3f})")
    ax.plot(strict_metrics['fpr'], strict_metrics['tpr'], 'r-', lw=2,
            label=f"Strict (AUC = {strict_metrics['auc']:.3f})")
    ax.plot([0, 1], [0, 1], 'k--', lw=1, label='Random (AUC = 0.500)')
    ax.set_xlabel('False Positive Rate')
    ax.set_ylabel('True Positive Rate')
    ax.set_title('ROC Curves: Loose vs Strict', fontweight='bold')
    ax.legend(loc='lower right')
    ax.grid(alpha=0.3)
    
    # 2. Risk Score Distributions - Loose
    ax = axes[0, 1]
    ax.hist(bmw_loose['Risk_Score'], bins=20, alpha=0.6, label='BMW 2014', color='green')
    ax.hist(vw_loose['Risk_Score'], bins=20, alpha=0.6, label='VW 2014', color='red')
    ax.set_xlabel('Risk Score')
    ax.set_ylabel('Frequency')
    ax.set_title('Risk Score Distribution - Loose Classifier', fontweight='bold')
    ax.legend()
    ax.grid(alpha=0.3)
    
    # 3. Risk Score Distributions - Strict
    ax = axes[1, 0]
    ax.hist(bmw_strict['Risk_Score'], bins=20, alpha=0.6, label='BMW 2014', color='green')
    ax.hist(vw_strict['Risk_Score'], bins=20, alpha=0.6, label='VW 2014', color='red')
    ax.set_xlabel('Risk Score')
    ax.set_ylabel('Frequency')
    ax.set_title('Risk Score Distribution - Strict Classifier', fontweight='bold')
    ax.legend()
    ax.grid(alpha=0.3)
    
    # 4. AUC Comparison Bar Chart
    ax = axes[1, 1]
    classifiers = ['Loose', 'Strict']
    aucs = [loose_metrics['auc'], strict_metrics['auc']]
    colors = ['steelblue', 'coral']
    
    bars = ax.bar(classifiers, aucs, color=colors, alpha=0.8)
    ax.set_ylabel('AUC', fontsize=12)
    ax.set_title('AUC Comparison', fontweight='bold', fontsize=12)
    ax.set_ylim([0.5, 1.0])
    ax.axhline(y=0.5, color='k', linestyle='--', alpha=0.3, label='Random')
    ax.axhline(y=0.7, color='orange', linestyle='--', alpha=0.3, label='Acceptable')
    ax.axhline(y=0.9, color='green', linestyle='--', alpha=0.3, label='Excellent')
    ax.grid(axis='y', alpha=0.3)
    ax.legend()
    
    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.3f}',
                ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    viz_file = RESULTS_DIR / "sentence_level_auc_analysis.png"
    plt.savefig(viz_file, dpi=300, bbox_inches='tight')
    print(f"✅ Visualization saved: {viz_file}")
    
    # =========================
    # SAVE RESULTS
    # =========================
    
    results_df = pd.DataFrame({
        'Classifier': ['Loose', 'Strict'],
        'AUC': [loose_metrics['auc'], strict_metrics['auc']],
        'Optimal_Threshold': [loose_metrics['optimal_threshold'], strict_metrics['optimal_threshold']],
        'TPR_at_optimal': [loose_metrics['optimal_tpr'], strict_metrics['optimal_tpr']],
        'FPR_at_optimal': [loose_metrics['optimal_fpr'], strict_metrics['optimal_fpr']],
        'Interpretation': [interpret_auc(loose_metrics['auc']), interpret_auc(strict_metrics['auc'])],
        'BMW_Mean_Score': [bmw_loose['Risk_Score'].mean(), bmw_strict['Risk_Score'].mean()],
        'VW_Mean_Score': [vw_loose['Risk_Score'].mean(), vw_strict['Risk_Score'].mean()],
        'Mean_Separation': [
            vw_loose['Risk_Score'].mean() - bmw_loose['Risk_Score'].mean(),
            vw_strict['Risk_Score'].mean() - bmw_strict['Risk_Score'].mean()
        ]
    })
    
    output_file = RESULTS_DIR / "sentence_level_auc_results.xlsx"
    results_df.to_excel(output_file, index=False)
    print(f"✅ Results saved: {output_file}")
    
    # =========================
    # FINAL RECOMMENDATION
    # =========================
    
    print("\n" + "="*80)
    print("FINAL RECOMMENDATION")
    print("="*80 + "\n")
    
    if winner == "STRICT":
        print(f"🏆 STRICT CLASSIFIER RECOMMENDED")
        print(f"   • Higher AUC: {strict_metrics['auc']:.4f} vs {loose_metrics['auc']:.4f}")
        print(f"   • Better at ranking quality above greenwashing")
        print(f"   • {interpret_auc(strict_metrics['auc'])} discrimination ability")
    elif winner == "LOOSE":
        print(f"🏆 LOOSE CLASSIFIER RECOMMENDED")
        print(f"   • Higher AUC: {loose_metrics['auc']:.4f} vs {strict_metrics['auc']:.4f}")
        print(f"   • Better at ranking quality above greenwashing")
        print(f"   • {interpret_auc(loose_metrics['auc'])} discrimination ability")
    else:
        print(f"⚖️  BOTH CLASSIFIERS PERFORM SIMILARLY")
        print(f"   • AUC difference < 0.05 (not significant)")
        print(f"   • Both have {interpret_auc(loose_metrics['auc'])} discrimination")
        print(f"   • Choose based on other criteria (interpretability, granularity)")
    
    print("\n" + "="*80)
    print("\nThis analysis answers: 'How good is each classifier at ranking")
    print("quality sentences as lower risk than greenwashing sentences?'")
    print("\nHigher AUC = better ranking ability = better classifier")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()