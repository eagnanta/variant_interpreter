import pandas as pd
import re

df = pd.read_csv("data/interpretations_final.csv")

def extract_llm_verdict(text):
    """Extract functional verdict from LLM interpretation."""
    if pd.isna(text) or text.startswith("ERROR"):
        return "error"
    
    text = text.lower()
    
    # Look for damage-related language in points 2 and 3
    damaging_keywords = [
        "deleterious", "probably damaging", "likely damaging",
        "significant effect", "damaging to protein", "pathogenic"
    ]
    neutral_keywords = [
        "tolerated", "benign", "likely benign", "not damaging",
        "no significant effect", "neutral"
    ]
    uncertain_keywords = [
        "uncertain", "unclear", "cannot determine",
        "conflicting", "not available"
    ]
    
    damage_score = sum(1 for k in damaging_keywords if k in text)
    neutral_score = sum(1 for k in neutral_keywords if k in text)
    uncertain_score = sum(1 for k in uncertain_keywords if k in text)
    
    if damage_score > neutral_score and damage_score > uncertain_score:
        return "damaging"
    elif neutral_score > damage_score and neutral_score > uncertain_score:
        return "neutral"
    else:
        return "uncertain"

def clinvar_to_expected(significance):
    """Map ClinVar significance to expected functional verdict."""
    sig = str(significance).lower()
    if "pathogenic" in sig and "likely" not in sig:
        return "damaging"
    elif "likely pathogenic" in sig:
        return "damaging"
    elif "benign" in sig and "likely" not in sig:
        return "neutral"
    elif "likely benign" in sig:
        return "neutral"
    elif "uncertain" in sig:
        return "uncertain"
    else:
        return "unknown"

# Extract verdicts
df["llm_verdict"] = df["llm_interpretation"].apply(extract_llm_verdict)
df["expected_verdict"] = df["significance_clean"].apply(clinvar_to_expected)

# Calculate agreement
df["agreement"] = df["llm_verdict"] == df["expected_verdict"]

# Overall agreement
total = len(df)
agreed = df["agreement"].sum()
print(f"=== Overall Agreement ===")
print(f"Total variants: {total}")
print(f"Agreed: {agreed}")
print(f"Agreement rate: {agreed/total*100:.1f}%")

# Agreement by significance category
print(f"\n=== Agreement by ClinVar Category ===")
for cat in df["significance_clean"].unique():
    subset = df[df["significance_clean"] == cat]
    rate = subset["agreement"].mean() * 100
    print(f"{cat}: {rate:.1f}% ({subset['agreement'].sum()}/{len(subset)})")

# Agreement by gene
print(f"\n=== Agreement by Gene ===")
for gene in df["GeneSymbol"].unique():
    subset = df[df["GeneSymbol"] == gene]
    rate = subset["agreement"].mean() * 100
    print(f"{gene}: {rate:.1f}% ({subset['agreement'].sum()}/{len(subset)})")

# Disagreement cases — most interesting for analysis
print(f"\n=== Disagreement Cases ===")
disagreements = df[~df["agreement"]]
print(disagreements[["GeneSymbol", "significance_clean", 
                       "consequence", "llm_verdict", 
                       "expected_verdict"]].to_string())

# Save results
df.to_csv("data/evaluation_results.csv", index=False)
print(f"\nSaved to data/evaluation_results.csv ✓")
