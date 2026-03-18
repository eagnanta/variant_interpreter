from groq import Groq
import pandas as pd

# Initialize client
import os
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Load our enriched dataset
df = pd.read_csv("data/variants_cosmic.csv")

# Pick one TP53 pathogenic variant to test
test_variant = df[
    (df["GeneSymbol"] == "TP53") & 
    (df["significance_clean"] == "Pathogenic")
].iloc[0]

print("Testing with variant:")
print(f"Gene: {test_variant['GeneSymbol']}")
print(f"Variant: {test_variant['Name']}")
print(f"Significance: {test_variant['significance_clean']}")
print(f"Consequence: {test_variant['consequence']}")
print(f"Impact: {test_variant['impact']}")
print(f"SIFT: {test_variant['sift_score']}")
print(f"PolyPhen: {test_variant['polyphen_score']}")
print(f"COSMIC match: {test_variant['cosmic_match']}")
print("-" * 50)

# Handle missing values gracefully
sift = f"{test_variant['sift_score']}" if pd.notna(test_variant['sift_score']) else "not available"
polyphen = f"{test_variant['polyphen_score']}" if pd.notna(test_variant['polyphen_score']) else "not available"
cosmic_info = f"Yes, observed in {test_variant['cosmic_count']} tumor samples in COSMIC" if test_variant['cosmic_match'] else "No COSMIC match found"

# Build the prompt
prompt = f"""You are a clinical genomics assistant. Based ONLY on the evidence provided below,
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
Gene: {test_variant['GeneSymbol']}
Variant: {test_variant['Name']}
Clinical Significance: {test_variant['significance_clean']}
Consequence: {test_variant['consequence']}
Impact: {test_variant['impact']}
SIFT score: {sift}
PolyPhen score: {polyphen}
COSMIC evidence: {cosmic_info}
Publications: {test_variant['pubmed_pmids']}"""

# Call the API
try:
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    interpretation = response.choices[0].message.content
    print("\nLLM INTERPRETATION:")
    print(interpretation)
except Exception as e:
    print(f"\nERROR: {e}")
