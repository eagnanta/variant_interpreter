import pandas as pd
import requests
import time
import json

# Load our clean dataset
df = pd.read_csv("data/variants_clean.csv")

ENSEMBL_URL = "https://rest.ensembl.org/variant_recoder/human"
HEADERS = {"Content-Type": "application/json", "Accept": "application/json"}

def get_annotation(variant_name, gene):
    """Get VEP annotation for a variant using Ensembl REST API."""
    try:
        # Use the variant consequence endpoint
        url = f"https://rest.ensembl.org/vep/human/hgvs/{requests.utils.quote(variant_name)}"
        params = {
            "content-type": "application/json",
            "CADD": "1",
            "sift": "b",
            "polyphen": "b"
        }
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                result = data[0]
                # Extract most severe consequence
                consequence = result.get("most_severe_consequence", "unknown")
                
                # Extract transcript consequences
                transcript_data = result.get("transcript_consequences", [{}])
                if transcript_data:
                    tc = transcript_data[0]
                    sift = tc.get("sift_score", None)
                    polyphen = tc.get("polyphen_score", None)
                    impact = tc.get("impact", "unknown")
                    amino_acids = tc.get("amino_acids", None)
                    protein_pos = tc.get("protein_start", None)
                else:
                    sift = polyphen = impact = amino_acids = protein_pos = None
                
                return {
                    "consequence": consequence,
                    "impact": impact,
                    "sift_score": sift,
                    "polyphen_score": polyphen,
                    "amino_acids": amino_acids,
                    "protein_position": protein_pos,
                    "annotation_status": "success"
                }
        
        return {"annotation_status": f"failed_{response.status_code}"}
    
    except Exception as e:
        return {"annotation_status": f"error_{str(e)[:50]}"}


# Annotate all variants
print(f"Annotating {len(df)} variants...")
print("This will take a few minutes (API rate limit: 1 request/second)\n")

annotations = []
for i, row in df.iterrows():
    variant = row["Name"]
    gene = row["GeneSymbol"]
    
    print(f"[{i+1}/{len(df)}] {gene}: {variant[:50]}")
    
    ann = get_annotation(variant, gene)
    annotations.append(ann)
    
    # Respect API rate limit
    time.sleep(1)

# Merge annotations with original dataframe
ann_df = pd.DataFrame(annotations)
df_annotated = pd.concat([df.reset_index(drop=True), ann_df], axis=1)

# Summary
print("\n--- Annotation Summary ---")
print(f"Successful: {(ann_df['annotation_status'] == 'success').sum()}")
print(f"Failed: {(ann_df['annotation_status'] != 'success').sum()}")
print("\nConsequence breakdown:")
print(df_annotated["consequence"].value_counts())
print("\nImpact breakdown:")
print(df_annotated["impact"].value_counts())

df_annotated.to_csv("data/variants_annotated.csv", index=False)
print("\nSaved to data/variants_annotated.csv ✓")
