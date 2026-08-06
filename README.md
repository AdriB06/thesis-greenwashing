# Computational Framework for Greenwashing Detection in Automotive Sustainability Reporting

Bachelor's Thesis — THI Ingolstadt  
Author: Adriana Baba

---

## Overview

This repository contains the full pipeline for detecting greenwashing in automotive sustainability reports using a sentence-level LLM classification system built on Claude Sonnet (Anthropic API) with Pydantic structured output validation.

Five automotive manufacturers are analyzed across three reporting years (2020, 2022, 2024):
- BMW Group (Annual Report)
- Renault Group (Universal Registration Document)
- Tesla (Impact Report)
- Toyota Motor Corporation (Sustainability Data Book)
- BYD Company Limited (CSR Report)

Additional cases included: BMW 2014 and Volkswagen 2014 (Dieselgate external validation).

---

## Repository Structure

```
thesis-greenwashing/
│
├── data/
│   ├── cleaned_text/          # Cleaned plain text files ready for classification
│   │   ├── BMW_2014_Sustainability_clean.txt
│   │   ├── BMW_2020_Sustainability_clean.txt
│   │   ├── BMW_2022_Sustainability_clean.txt
│   │   ├── BMW_2024_Sustainability_clean.txt
│   │   ├── BYD_2020_Sustainability_clean.txt
│   │   ├── BYD_2022_Sustainability_clean.txt
│   │   ├── BYD_2024_Sustainability_clean.txt
│   │   ├── Renault_2020_Sustainability_clean.txt
│   │   ├── Renault_2022_Sustainability_clean.txt
│   │   ├── Renault_2024_Sustainability_clean.txt
│   │   ├── Tesla_2020_Sustainability_clean.txt
│   │   ├── Tesla_2022_Sustainability_clean.txt
│   │   ├── Tesla_2024_Sustainability_clean.txt
│   │   ├── Toyota_2020_Sustainability_clean.txt
│   │   ├── Toyota_2022_Sustainability_clean.txt
│   │   ├── Toyota_2024_Sustainability_clean.txt
│   │   ├── VW_2014_Sustainability_clean.txt
│   │   ├── Synthetic_2024_clean.txt       # Synthetic sentences for validation
│   │   └── synthetic_sentences.xlsx       # Synthetic sentence dataset (n=170)
│   │
│   ├── raw_pdfs/              # Original source PDF files
│   │   ├── BMW_Group_Annual_Report_2012.pdf
│   │   ├── 2014-BMW-Group-Annual-Report.pdf
│   │   ├── BMW-Group-Bericht-2020-EN.pdf
│   │   ├── BMW-Group-Report-2022-en.pdf
│   │   ├── BMW-Group-Report-2024-en.pdf
│   │   ├── BYD_sustainability_report_2020.pdf     # Image-based, OCR required
│   │   ├── BYD_sustainability_report_2020.pdf.txt # OCR output from professor
│   │   ├── BYD_sustainability_report_2022.pdf
│   │   ├── BYD_sustainability_report_2024.pdf
│   │   ├── RENAULT_2020-URD-EN-ecobook.pdf
│   │   ├── Renault_urd_2022_en.pdf
│   │   ├── Renault_URD_2024_EN.pdf
│   │   ├── Toyota_sustainability_data_book_2020.pdf
│   │   ├── Toyota_sustainability_data_book_2022.pdf
│   │   ├── Toyota_sustainability_data_book_2024.pdf
│   │   ├── 2020-tesla-impact-report.pdf
│   │   ├── 2022-tesla-impact-report.pdf
│   │   ├── 2024-extended-version-tesla-impact-report.pdf
│   │   └── 2014-Annual-Report.pdf                # VW 2014 external validation
│   │
│   └── raw_text/              # Raw extracted text before cleaning
│       ├── BMW_2014_Sustainability_raw.txt
│       ├── BMW_2020_Sustainability_raw.txt
│       ├── BMW_2022_Sustainability_raw.txt
│       ├── BMW_2024_Sustainability_raw.txt
│       ├── BYD_2020_Sustainability_raw.txt
│       ├── BYD_2022_Sustainability_raw.txt
│       ├── BYD_2024_Sustainability_raw.txt
│       ├── Renault_2020_Sustainability_raw.txt
│       ├── Renault_2022_Sustainability_raw.txt
│       ├── Renault_2024_Sustainability_raw.txt
│       ├── Tesla_2020_Sustainability_raw.txt
│       ├── Tesla_2022_Sustainability_raw.txt
│       ├── Tesla_2024_Sustainability_raw.txt
│       ├── Toyota_2020_Sustainability_raw.txt
│       ├── Toyota_2022_Sustainability_raw.txt
│       ├── Toyota_2024_Sustainability_raw.txt
│       └── VW_2014_Sustainability_raw.txt
│
├── results/
│   ├── strict_classifier results/    # Main classification outputs
│   │   ├── BMW_2014_strict_classified.xlsx
│   │   ├── BMW_2014_strict_indicators.xlsx
│   │   ├── BMW_2020_strict_classified.xlsx
│   │   ├── BMW_2020_strict_indicators.xlsx
│   │   ├── BMW_2022_strict_classified.xlsx
│   │   ├── BMW_2022_strict_indicators.xlsx
│   │   ├── BMW_2024_strict_classified.xlsx
│   │   ├── BMW_2024_strict_indicators.xlsx
│   │   ├── BYD_2020_strict_classified.xlsx
│   │   ├── BYD_2020_strict_indicators.xlsx
│   │   ├── BYD_2022_strict_classified.xlsx
│   │   ├── BYD_2022_strict_indicators.xlsx
│   │   ├── BYD_2024_strict_classified.xlsx
│   │   ├── BYD_2024_strict_indicators.xlsx
│   │   ├── Renault_2020_strict_classified.xlsx
│   │   ├── Renault_2020_strict_indicators.xlsx
│   │   ├── Renault_2022_strict_classified.xlsx
│   │   ├── Renault_2022_strict_indicators.xlsx
│   │   ├── Renault_2024_strict_classified.xlsx
│   │   ├── Renault_2024_strict_indicators.xlsx
│   │   ├── Tesla_2020_strict_classified.xlsx
│   │   ├── Tesla_2020_strict_indicators.xlsx
│   │   ├── Tesla_2022_strict_classified.xlsx
│   │   ├── Tesla_2022_strict_indicators.xlsx
│   │   ├── Tesla_2024_strict_classified.xlsx
│   │   ├── Tesla_2024_strict_indicators.xlsx
│   │   ├── Toyota_2020_strict_classified.xlsx
│   │   ├── Toyota_2020_strict_indicators.xlsx
│   │   ├── Toyota_2022_strict_classified.xlsx
│   │   ├── Toyota_2022_strict_indicators.xlsx
│   │   ├── Toyota_2024_strict_classified.xlsx
│   │   ├── Toyota_2024_strict_indicators.xlsx
│   │   ├── VW_2014_strict_classified.xlsx
│   │   └── VW_2014_strict_indicators.xlsx
│   │
│   ├── loose_classifier results/     # Loose threshold classifier outputs
│   │
│   └── validation/
│       ├── classifier_selection/     # AUC and ROC analysis
│       │   ├── figure1_per_category.png
│       │   ├── figure2_main_analysis.png
│       │   ├── sentence_level_auc_analysis.png
│       │   ├── sentence_level_auc_results.xlsx
│       │   └── threshold_sweep_results.xlsx
│       │
│       ├── kappa_analysis/           # Inter-rater reliability
│       │   ├── kappa_annotation_sample.xlsx
│       │   ├── kappa_annotation_sample_annotated.xlsx
│       │   └── kappa_results.xlsx
│       │
│       └── synthetic_evaluation/     # Synthetic sentence validation
│           ├── Synthetic_2024_strict_classified.xlsx
│           ├── Synthetic_2024_strict_classified.jsonl
│           ├── synthetic_evaluation_results.xlsx
│           ├── synthetic_roc_threshold_sweep.xlsx
│           ├── synthetic_roc_validation.png
│           └── synthetic_sentences_with_categories.xlsx
│
├── scripts/                   # Extraction and cleaning scripts
│   ├── extract_bmw_2014.py
│   ├── extract_bmw_2020.py
│   ├── extract_bmw_2022.py
│   ├── extract_bmw_2024.py
│   ├── extract_byd_2022.py
│   ├── extract_byd_2024.py
│   ├── extract_renault_2020.py
│   ├── extract_renault_2022.py
│   ├── extract_renault_2024.py
│   ├── extract_tesla_2020.py
│   ├── extract_tesla_2022.py
│   ├── extract_tesla_2024.py
│   ├── extract_toyota_2020.py
│   ├── extract_toyota_2022.py
│   ├── extract_toyota_2024.py
│   ├── extract_VW_2014.py
│   ├── clean_bmw_2014.py
│   ├── clean_bmw_2020.py
│   ├── clean_bmw_2022.py
│   ├── clean_bmw_2024.py
│   ├── clean_byd_2020.py
│   ├── clean_byd_2022.py
│   ├── clean_byd_2024.py
│   ├── clean_renault_2020.py
│   ├── clean_renault_2022.py
│   ├── clean_renault_2024.py
│   ├── clean_tesla_2020.py
│   ├── clean_tesla_2022.py
│   ├── clean_tesla_2024.py
│   ├── clean_toyota_2020.py
│   ├── clean_toyota_2022.py
│   ├── clean_toyota_2024.py
│   └── clean_VW_2014.py
│
└── src/                       # Core pipeline source code
    ├── strict_classifier.py          # Main LLM classification pipeline
    ├── calculate_indicators.py       # Greenwashing indicator computation
    ├── run_pipeline.py               # End-to-end pipeline runner
    ├── schema.py                     # Pydantic output schema
    ├── kappa_analysis.py             # Cohen's Kappa inter-rater analysis
    ├── loose_classifier.py           # Loose threshold classifier
    ├── sample_kappa.py               # Kappa sampling utility
    ├── sentence_level_AUC_analysis.py
    └── strict_classifier_ROC_analysis.py
|
└── test_key.py 
```

---

## Pipeline Overview

```
PDF / TXT
   ↓
extract_*.py          → raw_text/
   ↓
clean_*.py            → cleaned_text/
   ↓
strict_classifier.py  → *_strict_classified.xlsx
   ↓
calculate_indicators.py → *_strict_indicators.xlsx
```

## Requirements

```
anthropic
pydantic
pdfplumber
pymupdf
pytesseract
pandas
openpyxl
scikit-learn
```

Install with:
```bash
pip install -r requirements.txt
```

---

## Model

All classification uses **Claude Sonnet** via the Anthropic API.  
See `src/schema.py` for the Pydantic output schema and `Appendix B` of the thesis for the classification prompt.
