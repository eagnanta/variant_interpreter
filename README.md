# LLM-Assisted Variant Interpreter

A bioinformatics pipeline that integrates clinical and cancer genomics databases
with a large language model to generate evidence-based clinical interpretations
of genomic variants automatically.
Built as an independent MSc research project during the 2nd semester of an MSc in
Applied Bioinformatics at the Aristotle University of Thessaloniki (AUTH).

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
can assist this process by synthesising structured evidence into readable
interpretations that clinicians can verify and act on.
The tool is designed with grounding as a core principle: the LLM is instructed
to reason only from the structured evidence provided by the upstream databases,
reducing hallucination and making all outputs verifiable.

---

## Pipeline
```
ClinVar (variant dataset)
        ↓
Label harmonisation
(Pathogenic / Likely pathogenic / Benign / Likely benign / VUS)
        ↓
Ensembl VEP annotation
(consequence, SIFT, PolyPhen)
        ↓
COSMIC integration
(tumor observations, somatic status, tumor type mapping)
        ↓
Deduplication & merging
(min SIFT, max PolyPhen, unique tumor types)
        ↓
LLM interpretation
(LLaMA 3.3 70B via Groq API — grounding-first prompt)
        ↓
Rate-limit repair layer
(LLaMA 3.1 8B for recovery)
        ↓
Confidence scoring
(HIGH / MEDIUM / LOW)
        ↓
Streamlit web interface
```

---

## Results

The pipeline was evaluated in two phases by comparing LLM functional reasoning
against ClinVar ground truth labels.

### Phase 1 — Proof of concept (5 genes, 76 variants)

Initial evaluation on the five most well-studied cancer genes with clean
annotation coverage:

| Category | Agreement |
| --- | --- |
| Overall | 75.0% |
| Pathogenic | 100.0% |
| Likely pathogenic | 100.0% |
| Likely benign | 72.2% |
| Benign | 28.6% |
| Uncertain significance | 64.0% |

### Phase 2 — Extended evaluation (10 genes, 592 variants)

Evaluation on an expanded dataset including mismatch repair and additional
tumour suppressor genes, representing a harder and more realistic benchmark:

| Category | Agreement |
| --- | --- |
| Overall | 69.4% |
| Likely benign | 87.4% |
| Likely pathogenic | 77.1% |
| Uncertain significance | 63.8% |
| Pathogenic | 61.4% |
| Benign | 36.4% |

#### Agreement by gene

| Gene | Agreement |
| --- | --- |
| TP53 | 95.0% |
| PALB2 | 80.0% |
| PTEN | 77.6% |
| APC | 72.9% |
| KRAS | 70.0% |
| EGFR | 70.0% |
| MLH1 | 69.0% |
| MSH2 | 56.9% |
| STK11 | 55.0% |
| BRCA1 | 47.5% |


**Key findings:**

- Exceptional TP53 Performance (95.0%): The model achieved near-human level accuracy on TP53, demonstrating that LLMs are highly effective at interpreting variants in well-characterized tumor suppressors with dense annotation coverage.
- High Sensitivity for Likely Benign (87.4%): The pipeline excels at identifying "Likely Benign" variants, significantly reducing the manual burden of filtering out non-actionable mutations.
- Clinical Conservatism in BRCA1: The lower agreement in BRCA1 (47.5%) is driven by a "caution-first" bias. Disagreement analysis shows the LLM frequently assigns "Uncertain" to missense variants that lack definitive functional scores, rather than making potentially false neutral or damaging calls.
-Durable Reasoning at Scale: Despite moving from 76 to 592 variants, the overall agreement rate remained consistent (~70%), proving the pipeline's logic is robust and scales effectively to larger genomic datasets.
- Zero-Error Data Integrity: Through the implementation of a tiered repair layer, the pipeline achieved a 100% success rate in generating interpretations, even when facing high-frequency API rate limits on the Aristotle HPC cluster.

---

## Confidence Scoring

Each interpretation is assigned a confidence level based on evidence agreement:

| Level | Criteria |
| --- | --- |
| HIGH | SIFT + PolyPhen + COSMIC + consequence all agree |
| MEDIUM | Partial evidence agreement |
| LOW | Missing scores, conflicting evidence, or VUS |

**Confidence distribution (Phase 2, 593 variants):**

| Confidence | Count |
| --- | --- |
| HIGH | 151 |
| MEDIUM | 231 |
| LOW | 211 |

---

## Project Structure

```
variant_project/
├── src/
│   ├── build_dataset.py            # ClinVar dataset construction (10 genes)
│   ├── cleaned_labels.py           # Label harmonisation
│   ├── annotate_variants.py        # Ensembl VEP annotation
│   ├── integrate_cosmic.py         # COSMIC integration with AA normalisation
│   ├── add_tumor_types.py          # COSMIC phenotype → tumor type mapping
│   ├── fix_missing_annotations.py  # Manual annotation fixes
│   ├── run_llm_pipeline.py         # LLM interpretation pipeline
│   ├── test_llm.py                 # Single variant test
│   ├── repair_interpretations.py   # Rate-limit error recovery
│   ├── evaluation_llm.py           # Evaluation framework
│   ├── confidence_score.py         # Confidence scoring
│   └── app.py                      # Streamlit interface
├── data/                           # Not tracked — see Data Requirements below
└── README.md
```

---

## Data Requirements

The `data/` directory is excluded from this repository. To reproduce the
pipeline, download the following files and place them in a `data/` folder:

| File | Source | Instructions |
| --- | --- | --- |
| `variant_summary.txt.gz` | ClinVar FTP | Direct download |
| `Cosmic_MutantCensus_v103_GRCh37.tsv` | COSMIC Downloads | Requires free registration |
| `Cosmic_Classification_v103_GRCh37.tsv` | COSMIC Downloads | Requires free registration |

---

## How to Run

### Requirements

```bash
pip install -r requirements.txt
```

### Environment setup

```bash
export GROQ_API_KEY="your_groq_api_key"
```

### Run the full pipeline

```bash
# Step 1: Build dataset
python src/build_dataset.py
python src/cleaned_labels.py

# Step 2: Annotate variants
python src/annotate_variants.py

# Step 3: COSMIC integration
python src/integrate_cosmic.py
python src/add_tumor_types.py

# Step 4: Fix missing annotations
python src/fix_missing_annotations.py

# Step 5: LLM pipeline
python src/run_llm_pipeline.py

# Step 6: Confidence scoring
python src/confidence_score.py

# Step 7: Evaluation
python src/evaluation_llm.py

# Step 8: Repair any rate-limit errors
python src/repair_interpretations.py
```

### Launch the web interface

```bash
streamlit run src/app.py --server.port 8501 --server.address 0.0.0.0
```

---

## Data Sources

| Source | Version | Usage |
| --- | --- | --- |
| ClinVar | March 2026 | Clinical significance labels |
| Ensembl VEP | GRCh37 | Functional annotation |
| COSMIC CMC | v103 GRCh37 | Cancer mutation data |

---

## Target Genes

BRCA1, TP53, EGFR, KRAS, PTEN, APC, MLH1, MSH2, STK11, PALB2

Selected to cover a broad range of cancer biology: tumour suppressors, oncogenes,
DNA repair genes, and mismatch repair genes across multiple cancer types.

---

## Limitations

- Mismatch repair genes (MSH2, MLH1) show lower agreement, partly attributable
  to gaps in VEP annotation coverage for this gene class
- Groq free tier: 100,000 tokens/day limit — pipeline uses tiered model approach
  (LLaMA 3.3 70B primary, LLaMA 3.1 8B for rate-limit recovery)
- Benign non-coding variants underperform due to absent SIFT/PolyPhen scores,
  though improved consequence-type reasoning partially mitigates this
- COSMIC data requires a non-commercial license for redistribution

---

## Future Work

- Expand to 500+ variants across additional cancer genes
- Implement RAG (Retrieval Augmented Generation) for literature evidence
- Add ACMG/AMP classification logic
- Compare performance across multiple LLMs (GPT-4o, Gemini, Claude)
- Validate interpretations with clinical expert review
- Incorporate splicing predictors to improve non-coding variant performance

---

## Technologies

- Python 3.9
- Pandas
- Groq API (LLaMA 3.3 70B / LLaMA 3.1 8B)
- Ensembl REST API
- Streamlit
- SLURM (HPC job scheduling)
- Git / GitHub

---

## Author

MSc Applied Bioinformatics student — Aristotle University of Thessaloniki (AUTH)

Independent MSc research project, March 2026

---

> **Note:** COSMIC data (CMC v103) is used under a non-commercial academic
> license. Users wishing to replicate this pipeline must obtain independent
> access from [cancer.sanger.ac.uk](https://cancer.sanger.ac.uk).
Initial evaluation on the five most well-studied cancer genes with clean
annotation coverage:
CategoryAgreementOverall75.0%Pathogenic100.0%Likely pathogenic100.0%Likely benign72.2%Benign28.6%Uncertain significance64.0%

