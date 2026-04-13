import pandas as pd
import os
import time
from groq import Groq

# Initialize client
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Load enriched dataset
df_raw = pd.read_csv("data/variants_cosmic.csv")

# Define Clinical Merge rules
aggregation_rules = {
    'significance_clean': 'first',
    'consequence': 'first',
    'impact': 'first',
    'sift_score': 'min',         # SIFT: lowest score is most deleterious
    'polyphen_score': 'max',      # PolyPhen: highest score is most damaging
    'cosmic_match': 'max',        # True if any entry matched COSMIC
    'cosmic_count': 'sum',        # Total count across all duplicate entries
    'tumor_types': lambda x: '; '.join(set(filter(None, x.dropna().astype(str)))), # Unique tumors list
    'pubmed_pmids': 'first'
}

# Execute the Merge
df = df_raw.groupby(['Name', 'GeneSymbol'], as_index=False).agg(aggregation_rules)

# Load existing data into results
processed_variants = set()
results = []
output_file = "data/interpretations_final.csv"

if os.path.exists(output_file):
    try:
        existing_df = pd.read_csv(output_file)
        processed_variants = set(existing_df['Name'].dropna().tolist())
        # loads our old work into the list so it isn't lost
        results = existing_df.to_dict('records') 
        print(f"Resuming: {len(processed_variants)} variants already completed.")
    except Exception as e:
        print(f"Starting fresh: {e}")

def build_prompt(row):
    """Build clinical interpretation prompt for a single variant."""
    sift = f"{row['sift_score']}" if pd.notna(row['sift_score']) else "not available"
    polyphen = f"{row['polyphen_score']}" if pd.notna(row['polyphen_score']) else "not available"

    if row['cosmic_match']:
        # Use the joined tumor_types from the merge
        tumor_types = row['tumor_types'] if pd.notna(row.get('tumor_types')) else "unknown tumor types"
        cosmic_info = f"Yes, observed in {row['cosmic_count']} tumor samples. Tumor types: {tumor_types}"
    else:
        cosmic_info = "No COSMIC match found"

    return f"""You are a clinical genomics assistant. Based ONLY on the evidence provided below,
write a concise clinical interpretation of this variant.

Your interpretation must cover exactly these four points:
1. Classification: What is the ClinVar clinical significance of this variant?
2. Functional impact: Based on the SIFT score, is the amino acid change deleterious or tolerated?
3. Protein damage: Based on the PolyPhen score, is the variant probably damaging,
   possibly damaging, or benign?
4. Cancer evidence: Has this variant been observed in tumor samples in COSMIC?
   If yes, name the specific tumor types where it has been observed.

Write in clear clinical language. Do not add information beyond what is provided.
If SIFT and PolyPhen scores are not available, reason from the consequence type
instead — intronic, synonymous, and non-coding variants are generally less likely
to be damaging than missense or frameshift variants.
The following consequence types are generally damaging regardless of SIFT/PolyPhen
scores: frameshift_variant, stop_gained, splice_donor_variant,
splice_acceptor_variant, splice_donor_5th_base_variant, inframe_deletion,
inframe_insertion, copy_number_variation.
The following consequence types are generally benign regardless of SIFT/PolyPhen
scores: intron_variant, synonymous_variant, non_coding_transcript_exon_variant,
upstream_gene_variant.
Do not classify a variant as damaging based solely on the SIFT score — reason also
from the consequence type.
For variants of uncertain significance, clearly state that the clinical
classification is uncertain even if functional scores suggest possible damage.

VARIANT DATA:
Gene: {row['GeneSymbol']}
Variant: {row['Name']}
Clinical Significance: {row['significance_clean']}
Consequence: {row['consequence']}
Impact: {row['impact']}
SIFT score: {sift}
PolyPhen score: {polyphen}
COSMIC evidence: {cosmic_info}
Publications: {row['pubmed_pmids']}"""

def interpret_variant(row):
    """Call LLM API for a single variant with error handling."""
    try:
        prompt = build_prompt(row)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"ERROR: {str(e)}"

# Run pipeline
for i, row in df.iterrows():
    if row['Name'] in processed_variants:
        continue
    print(f"[{i+1}/{len(df)}] {row['GeneSymbol']}: {row['Name'][:50]}")

    interpretation = interpret_variant(row)
    results.append({
        "GeneSymbol": row["GeneSymbol"],
        "Name": row["Name"],
        "significance_clean": row["significance_clean"],
        "consequence": row["consequence"],
        "impact": row["impact"],
        "sift_score": row["sift_score"],
        "polyphen_score": row["polyphen_score"],
        "cosmic_match": row["cosmic_match"],
        "cosmic_count": row["cosmic_count"],
        "tumor_types": row.get("tumor_types"),
        "pubmed_pmids": row["pubmed_pmids"],
        "llm_interpretation": interpretation
    })


    # Mark as processed
    processed_variants.add(row['Name'])

    # Save progressively every 10 variants
    if (i + 1) % 10 == 0:
        pd.DataFrame(results).to_csv(output_file, index=False)
        print(f"Saved progress ({len(results)} total variants now in file)")

    # Respect rate limit
    time.sleep(10)

# Save final results
final_df = pd.DataFrame(results)
final_df.to_csv("data/interpretations_final.csv", index=False)

# Summary
print(f"\n--- Pipeline Summary ---")
print(f"Total variants processed: {len(final_df)}")
errors = final_df[final_df["llm_interpretation"].str.startswith("ERROR")]
print(f"Successful interpretations: {len(final_df) - len(errors)}")
print(f"Errors: {len(errors)}")
print("\nSaved to data/interpretations_final.csv ✓")
