import pandas as pd

df = pd.read_csv("data/variants_annotated.csv")

# Manual annotation for failed variants
manual = {
    "BRCA1, 6-KB DUP, EX13": {
        "consequence": "copy_number_variation",
        "impact": "HIGH",
        "annotation_status": "manual"
    },
    "NM_000314.4(PTEN):c.-1060C>G": {
        "consequence": "upstream_gene_variant",
        "impact": "MODIFIER",
        "annotation_status": "manual"
    },
    "NM_004985.5(KRAS):c.528GAA[3] (p.Lys180dup)": {
        "consequence": "inframe_insertion",
        "impact": "MODERATE",
        "annotation_status": "manual"
    }
}

for variant_name, annotations in manual.items():
    mask = df["Name"] == variant_name
    for col, val in annotations.items():
        df.loc[mask, col] = val

print("Fixed variants:")
fixed = df[df["annotation_status"] == "manual"]
print(fixed[["GeneSymbol", "Name", "consequence", "impact"]].to_string())

df.to_csv("data/variants_annotated.csv", index=False)
print("\nSaved to data/variants_annotated.csv ✓")
