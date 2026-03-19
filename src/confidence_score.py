import pandas as pd

def calculate_confidence(row):
    score = 0
    reasons = []

    sift = row['sift_score']
    polyphen = row['polyphen_score']
    cosmic = row['cosmic_match']
    consequence = str(row['consequence']) if pd.notna(row['consequence']) else ""
    significance = str(row['significance_clean'])

    damaging_consequences = [
        'frameshift_variant', 'stop_gained', 'splice_donor_variant',
        'splice_acceptor_variant', 'inframe_deletion', 'inframe_insertion',
        'copy_number_variation', 'splice_donor_5th_base_variant'
    ]

    benign_consequences = [
        'intron_variant', 'synonymous_variant',
        'non_coding_transcript_exon_variant', 'upstream_gene_variant'
    ]

    if pd.notna(sift):
        if sift < 0.05:
            score += 1
            reasons.append("SIFT deleterious")
        else:
            score -= 1
            reasons.append("SIFT tolerated")
    else:
        reasons.append("SIFT missing")

    if pd.notna(polyphen):
        if polyphen > 0.85:
            score += 1
            reasons.append("PolyPhen probably damaging")
        elif polyphen < 0.15:
            score -= 1
            reasons.append("PolyPhen benign")
        else:
            reasons.append("PolyPhen borderline")
    else:
        reasons.append("PolyPhen missing")

    if cosmic:
        score += 1
        reasons.append("COSMIC match found")
    else:
        score -= 1
        reasons.append("No COSMIC match")

    if consequence in damaging_consequences:
        score += 2
        reasons.append(f"Damaging consequence: {consequence}")
    elif consequence in benign_consequences:
        score -= 2
        reasons.append(f"Benign consequence: {consequence}")

    if pd.notna(sift) and pd.notna(polyphen):
        sift_damaging = sift < 0.05
        polyphen_damaging = polyphen > 0.85
        if sift_damaging != polyphen_damaging:
            reasons.append("SIFT/PolyPhen disagree")

    if "Uncertain" in significance:
        return "LOW", "; ".join(reasons)

    if abs(score) >= 3:
        confidence = "HIGH"
    elif abs(score) >= 1:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"

    return confidence, "; ".join(reasons)

# Load interpretations
df = pd.read_csv("data/interpretations_final.csv")

# Calculate confidence
confidences = []
reasons_list = []

for i, row in df.iterrows():
    confidence, reasons = calculate_confidence(row)
    confidences.append(confidence)
    reasons_list.append(reasons)

df["confidence"] = confidences
df["confidence_reasons"] = reasons_list

# Summary
print("=== Confidence Score Distribution ===")
print(df["confidence"].value_counts())
print()
print("=== Confidence by ClinVar Category ===")
print(df.groupby("significance_clean")["confidence"].value_counts().to_string())
print()
print("=== High Confidence examples ===")
high = df[df["confidence"] == "HIGH"]
print(high[["GeneSymbol", "significance_clean", "consequence", "confidence"]].head(10).to_string())

df.to_csv("data/interpretations_final.csv", index=False)
print("\nSaved confidence scores to interpretations_final.csv ✓")
