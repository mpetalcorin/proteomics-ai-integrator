import os
from dotenv import load_dotenv

load_dotenv()


def generate_ai_summary(analysis: dict, ml_result: dict):
    """
    This function provides a local rule-based AI-style report.
    You can later replace this with OpenAI, local LLM, or Ollama.
    """

    n_features = analysis.get("n_features", 0)
    n_samples = analysis.get("n_samples", 0)

    pc1 = analysis.get("explained_variance", {}).get("pc1", 0)
    pc2 = analysis.get("explained_variance", {}).get("pc2", 0)

    accuracy = ml_result.get("cross_validated_accuracy_mean", None)

    report = f"""
Proteomics AI Interpretation Report

This dataset contains {n_features} quantified molecular features across {n_samples} samples.

The PCA analysis shows that PC1 explains approximately {pc1:.2%} of the variation and PC2 explains approximately {pc2:.2%}. In simple terms, this tells us how much of the overall biological difference between samples can be compressed into the first two major patterns.

The most variable proteins or genes are likely to be biologically important because their abundance changes strongly across samples. These features may reflect disease biology, treatment response, metabolic rewiring, signalling changes, or technical variation.

"""

    if accuracy is not None:
        report += f"""
The machine-learning classifier achieved an estimated cross-validated accuracy of {accuracy:.2%}. This suggests that the protein abundance patterns contain predictive information that may separate biological groups such as tumour versus normal, treated versus untreated, or disease versus control samples.

However, this should be interpreted carefully. Small datasets can produce optimistic machine-learning results. The model should be validated using an independent external dataset before biological or clinical conclusions are made.
"""
    else:
        report += """
The machine-learning module could not confidently infer two sample groups. To enable prediction, rename the sample columns using labels such as Tumor, Normal, Treated, Control, Case, or Disease.
"""

    report += """
Recommended next steps:

1. Check sample naming and metadata.
2. Remove features with excessive missingness.
3. Apply biological group labels explicitly.
4. Run differential abundance analysis.
5. Map top proteins to pathways.
6. Validate candidate biomarkers experimentally.
7. Compare protein abundance with RNA, phosphoproteomics, or clinical data where available.
"""

    return report
