
import pandas as pd
import os
import time
from groq import Groq

# Initialize client
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Load enriched dataset
df = pd.read_csv("data/variants_cosmic.csv")

# Drop duplicates — same variant appears twice in our dataset
df = df.drop_duplicates(subset=["Name", "GeneSymbol"]).reset_index(drop=True)
print(f"Running LLM interpretation on {len(df)} unique variants...")

def build_prompt(row):
    """Build clinical interpretation prompt for a single variant."""
    sift = f"{row['sift_score']}" if pd.notna(row['sift_score']) else "not available"
    polyphen = f"{row['polyphen_score']}" if pd.notna(row['polyphen_score']) else "not available"
    cosmic_info = f"Yes, observed in {row['cosmic_count']} tumor samples in COSMIC" if row['cosmic_match'] else "No COSMIC match found"

    return f"""You are a clinical genomics assistant. Based ONLY on the evidence provided below,
write a concise clinical interpretation of this variant.

Your interpretation must cover exactly these four points:
1. Classification: What is the ClinVar clinical significance of this variant?
2. Functional impact: Based on the SIFT score, is the amino acid change deleterious or tolerated?
3. Protein damage: Based on the PolyPhen score, is the variant probably damaging,
   possibly damaging, or benign?
4. Cancer evidence: Has this variant been observed in tumor samples in COSMIC?

Write in clear clinical language. Do not add information beyond what is provided.
If a score is not available, state that clearly but use other available evidence
(consequence type, impact level, other scores) to still reason about the variant's
likely effect on protein function.

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
results = []
for i, row in df.iterrows():
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
        "llm_interpretation": interpretation
    })

    # Save progressively every 10 variants
    if (i + 1) % 10 == 0:
        pd.DataFrame(results).to_csv("data/interpretations_partial.csv", index=False)
        print(f"  → Saved progress ({i+1} variants done)")

    # Respect rate limit
    time.sleep(2)

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
