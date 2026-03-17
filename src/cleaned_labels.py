import pandas as pd

df = pd.read_csv("data/variants_clean.csv")

def simplify_significance(val):
    val = str(val).lower()
    if "pathogenic" in val and "likely" not in val:
        return "Pathogenic"
    elif "likely pathogenic" in val or "pathogenic/likely" in val:
        return "Likely pathogenic"
    elif "benign" in val and "likely" not in val:
        return "Benign"
    elif "likely benign" in val or "benign/likely" in val:
        return "Likely benign"
    elif "uncertain" in val:
        return "Uncertain significance"
    else:
        return "Other"

df["significance_clean"] = df["ClinicalSignificance"].apply(simplify_significance)

print("Cleaned significance:")
print(df["significance_clean"].value_counts())

df.to_csv("data/variants_clean.csv", index=False)
print("\nUpdated variants_clean.csv ") 
