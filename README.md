# LLM-Assisted Variant Interpreter

A bioinformatics pipeline that integrates clinical and cancer genomics databases 
with a large language model to generate evidence-based clinical interpretations 
of genomic variants automatically.

Built as an independent research project during the 2nd semester of an MSc in 
Applied Bioinformatics.

---

## What it does

This tool takes a genomic variant and automatically generates a clinical 
interpretation by:

1. Retrieving clinical significance from **ClinVar**
2. Annotating functional impact using **Ensembl VEP** (SIFT, PolyPhen scores)
3. Cross-referencing cancer observations in **COSMIC** (including automated mapping of Phenotype IDs to human-readable tumor types).
4. Generating a plain-language clinical interpretation using **LLaMA 3.3 70B** 
   via the Groq API
5. Assigning a **confidence score** based on evidence agreement

---

## Why it matters

Interpreting genomic variants is one of the most time-consuming tasks in clinical 
genomics. A single patient can carry thousands of variants, each requiring manual 
cross-referencing across multiple databases. This project demonstrates that LLMs 
can assist this process, by synthesizing structured evidence into readable 
interpretations that clinicians can verify and act on.

The tool is designed with **grounding** as a core principle: the LLM is 
instructed to reason only from provided evidence, reducing hallucination and 
making outputs verifiable.

---

## Pipeline
```
ClinVar (150 variants)
        ↓
Ensembl VEP annotation
(consequence, SIFT, PolyPhen)
        ↓
COSMIC integration
(tumor observations, somatic status)
        ↓
LLM interpretation
(LLaMA 3.3 70B via Groq API)
        ↓
Error Repair Layer
(LLaMA 3.1 8B for rate-limit recovery)
        ↓
Confidence scoring
(HIGH / MEDIUM / LOW)
        ↓
Streamlit web interface
```

---

## Results

The pipeline was evaluated by comparing LLM functional reasoning against 
ClinVar ground truth labels across 76 unique variants.

| Category | Agreement |
|---|---|
| Overall | 75.0% |
| Pathogenic | 100.0% |
| Likely pathogenic | 100.0% |
| Likely benign | 72.2% |
| Benign | 28.6% |
| Uncertain significance | 64.0% |

**Key findings:**
- The model achieves 100% agreement on Pathogenic and Likely Pathogenic variants
- Benign non-coding variants are systematically underperforming due to absent 
  SIFT/PolyPhen scores — an expected limitation of functional prediction tools
- Variants of Uncertain Significance consistently receive LOW confidence scores, 
  correctly reflecting genuine clinical ambiguity
- Disagreements cluster around missense VUS variants where functional evidence 
  conflicts with clinical classification — a biologically meaningful finding

---

## Confidence Scoring

Each interpretation is assigned a confidence level based on evidence agreement:

| Level | Criteria |
|---|---|
| HIGH | SIFT + PolyPhen + COSMIC + consequence all agree |
| MEDIUM | Partial evidence agreement |
| LOW | Missing scores, conflicting evidence, or VUS |

---

## Project Structure
```
variant_project/
├── data/
│   ├── variants_clean.csv          # 150 ClinVar variants
│   ├── variants_annotated.csv      # + Ensembl VEP annotation
│   ├── variants_cosmic.csv         # + COSMIC integration
│   ├── interpretations_final.csv   # + LLM interpretations + confidence
│   └── evaluation_results.csv      # Evaluation against ClinVar
├── src/
│   ├── build_dataset.py            # ClinVar dataset
│   ├── clean_labels.py             # Label harmonization
│   ├── annotate_variants.py        # Ensembl VEP annotation
│   ├── integrate_cosmic.py         # COSMIC integration
│   ├── fix_missing_annotations.py  # Manual annotation fixes
│   ├── run_llm_pipeline.py         # LLM interpretation pipeline
│   ├── test_llm.py                 # Single variant test
│   ├── evaluation_llm.py           # Evaluation framework
│   ├── confidence_score.py         # Confidence scoring
│   └── app.py                      # Streamlit interface
└── README.md
```

## Data Requirements

The `data/` directory is excluded from this repository. To reproduce the pipeline,
download the following files and place them in a `data/` folder:

| File | Source | Instructions |
|---|---|---|
| `variant_summary.txt.gz` | [ClinVar FTP](https://ftp.ncbi.nlm.nih.gov/pub/clinvar/tab_delimited/) | Direct download |
| `Cosmic_MutantCensus_v103_GRCh37.tsv` | [COSMIC Downloads](https://cancer.sanger.ac.uk/cosmic/download) | Requires free registration |
| `Cosmic_Classification_v103_GRCh37.tsv` | [COSMIC Downloads](https://cancer.sanger.ac.uk/cosmic/download) | Requires free registration |

---

## How to Run

### Requirements
```bash
pip install pandas requests groq streamlit
pip install pandas requests groq streamlit python-dotenv
```

### Environment setup
```bash
export GROQ_API_KEY="your_groq_api_key"
```

### Run the full pipeline
```bash
# Step 1: Build dataset
python src/build_dataset.py
python src/clean_labels.py

# Step 2: Annotate variants
python src/annotate_variants.py

# Step 3: COSMIC integration
python src/integrate_cosmic.py

# Step 4: Fix missing annotations
python src/fix_missing_annotations.py

# Step 5: LLM pipeline
python src/run_llm_pipeline.py

# Step 6: Confidence scoring
python src/confidence_score.py

# Step 7: Evaluation
python src/evaluation_llm.py

# Step 8: Repair any Rate-Limit/Connection errors
python src/repair_interpretations.py
```

### Launch the web interface
```bash
streamlit run src/app.py --server.port 8501 --server.address 0.0.0.0
```

---

## Data Sources

| Source | Version | Usage |
|---|---|---|
| ClinVar | March 2026 | Clinical significance labels |
| Ensembl VEP | GRCh37 | Functional annotation |
| COSMIC CMC | v103 GRCh37 | Cancer mutation data |

---

## Target Genes

BRCA1, TP53, EGFR, KRAS, PTEN

Selected for their established roles in cancer biology covering tumor suppressors,
oncogenes, and DNA repair genes across multiple cancer types.

---

## Limitations

- Dataset limited to 76 unique variants across 5 genes
- Groq free tier: 100,000 tokens/day limit
- Add: API Rate Management: Uses a tiered model approach (70B for primary, 8B for repair) to maximize Groq's daily token quota.
- Benign non-coding variants underperform due to absent functional scores
- COSMIC data requires non-commercial license for redistribution

---

## Future Work

- Expand to 500+ variants across more cancer genes
- Implement RAG (Retrieval Augmented Generation) for literature evidence
- Add ACMG classification logic
- Compare against other LLM models
- Validate interpretations with clinical expert review

---

## Technologies

- Python 3.9
- Pandas
- Groq API (LLaMA 3.3 70B)
- Ensembl REST API
- Streamlit
- SLURM (HPC job scheduling)
- Git/GitHub

---

## Author

MSc Applied Bioinformatics student — Aristotle University of Thessaloniki (AUTH)

*Built independently as a portfolio project, March 2026*
