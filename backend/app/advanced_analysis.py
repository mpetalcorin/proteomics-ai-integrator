import io
import base64
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.inspection import permutation_importance
import matplotlib.pyplot as plt


CONTROL_TERMS = ["normal", "control", "untreated", "vehicle", "healthy"]
CASE_TERMS = ["tumor", "tumour", "cancer", "treated", "case", "disease", "patient"]


def detect_fragpipe_tmt_integrator_format(df: pd.DataFrame):
    """
    Detects common FragPipe or TMT-Integrator-style tables.

    TMT-Integrator reports may use columns such as:
    Gene, Protein, Peptide, Index, gene, protein, peptide, or similar.

    The function chooses one identifier column and detects numeric sample columns.
    """
    possible_id_cols = [
        "Gene",
        "Genes",
        "gene",
        "genes",
        "Protein",
        "protein",
        "Protein ID",
        "protein_id",
        "Peptide",
        "peptide",
        "Index",
        "index",
        "feature",
        "Feature",
        "Entry",
        "entry",
    ]

    id_col = None

    for col in possible_id_cols:
        if col in df.columns:
            id_col = col
            break

    if id_col is None:
        id_col = df.columns[0]

    metadata_like = {
        id_col,
        "Description",
        "description",
        "Protein Description",
        "protein_description",
        "Entry Name",
        "entry_name",
        "Organism",
        "organism",
    }

    abundance_cols = []

    for col in df.columns:
        if col in metadata_like:
            continue

        converted = pd.to_numeric(df[col], errors="coerce")
        numeric_fraction = converted.notna().mean()

        if numeric_fraction > 0.6:
            abundance_cols.append(col)

    return id_col, abundance_cols


def prepare_abundance_matrix(df: pd.DataFrame):
    id_col, abundance_cols = detect_fragpipe_tmt_integrator_format(df)

    if len(abundance_cols) < 2:
        raise ValueError(
            "Could not detect enough numeric abundance columns. "
            "The file should contain one feature identifier column and at least two sample abundance columns."
        )

    identifiers = df[id_col].astype(str)

    numeric_df = df[abundance_cols].apply(pd.to_numeric, errors="coerce")
    numeric_df = numeric_df.replace([np.inf, -np.inf], np.nan)

    missing_percent = numeric_df.isna().mean(axis=1) * 100

    numeric_df = numeric_df.fillna(numeric_df.median())
    numeric_df = numeric_df.fillna(0)

    log_df = np.log2(numeric_df + 1)

    return {
        "id_col": id_col,
        "abundance_cols": abundance_cols,
        "identifiers": identifiers,
        "numeric_df": numeric_df,
        "log_df": log_df,
        "missing_percent": missing_percent,
    }


def infer_sample_groups(sample_names):
    control_cols = []
    case_cols = []

    for col in sample_names:
        lower = str(col).lower()

        if any(term in lower for term in CONTROL_TERMS):
            control_cols.append(col)

        if any(term in lower for term in CASE_TERMS):
            case_cols.append(col)

    return control_cols, case_cols


def differential_abundance(df: pd.DataFrame):
    prepared = prepare_abundance_matrix(df)

    identifiers = prepared["identifiers"]
    log_df = prepared["log_df"]
    missing_percent = prepared["missing_percent"]

    control_cols, case_cols = infer_sample_groups(log_df.columns)

    if len(control_cols) < 2 or len(case_cols) < 2:
        return {
            "warning": (
                "Differential analysis requires at least two control samples and two case samples. "
                "Use sample names such as Normal_1, Normal_2, Tumor_1, Tumor_2, "
                "Control_1, Control_2, Treated_1, Treated_2."
            ),
            "detected_columns": list(log_df.columns),
            "control_samples": control_cols,
            "case_samples": case_cols,
        }

    records = []

    for i in range(log_df.shape[0]):
        feature = str(identifiers.iloc[i])

        control_values = log_df.iloc[i][control_cols].astype(float).values
        case_values = log_df.iloc[i][case_cols].astype(float).values

        log2fc = float(np.mean(case_values) - np.mean(control_values))

        try:
            _, p_value = stats.ttest_ind(case_values, control_values, equal_var=False)
            if np.isnan(p_value):
                p_value = 1.0
        except Exception:
            p_value = 1.0

        records.append(
            {
                "feature": feature,
                "log2fc": log2fc,
                "p_value": float(p_value),
                "negative_log10_p": float(-np.log10(p_value + 1e-12)),
                "missing_percent": float(missing_percent.iloc[i]),
                "control_mean_log2": float(np.mean(control_values)),
                "case_mean_log2": float(np.mean(case_values)),
            }
        )

    result_df = pd.DataFrame(records)

    result_df["abs_log2fc"] = result_df["log2fc"].abs()

    result_df["biomarker_score"] = (
        result_df["abs_log2fc"] * result_df["negative_log10_p"]
    ) / (1 + result_df["missing_percent"] / 100)

    result_df = result_df.sort_values("biomarker_score", ascending=False)

    return {
        "control_samples": control_cols,
        "case_samples": case_cols,
        "n_features": int(result_df.shape[0]),
        "top_biomarkers": result_df.head(50).to_dict(orient="records"),
        "volcano_data": result_df.to_dict(orient="records"),
    }


def make_volcano_plot_base64(volcano_data):
    df = pd.DataFrame(volcano_data)

    if df.empty:
        return None

    fig, ax = plt.subplots(figsize=(8, 6))

    ax.scatter(
        df["log2fc"],
        df["negative_log10_p"],
        alpha=0.7,
        s=28,
    )

    ax.axvline(x=1, linestyle="--", linewidth=1)
    ax.axvline(x=-1, linestyle="--", linewidth=1)
    ax.axhline(y=-np.log10(0.05), linestyle="--", linewidth=1)

    ax.set_xlabel("log2 fold change")
    ax.set_ylabel("-log10 p-value")
    ax.set_title("Volcano Plot")

    top = df.sort_values("biomarker_score", ascending=False).head(10)

    for _, row in top.iterrows():
        ax.text(
            row["log2fc"],
            row["negative_log10_p"],
            str(row["feature"])[:18],
            fontsize=8,
        )

    fig.tight_layout()

    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=200)
    plt.close(fig)

    buffer.seek(0)
    encoded = base64.b64encode(buffer.read()).decode("utf-8")

    return encoded


def simple_pathway_enrichment(top_features):
    """
    Lightweight keyword-based pathway enrichment.

    This is not a replacement for Reactome, KEGG, or g:Profiler enrichment.
    It is a local first-pass biological annotation engine.
    """
    pathway_map = {
        "Glycolysis / Warburg metabolism": [
            "LDHA",
            "LDHB",
            "PKM",
            "HK1",
            "HK2",
            "GAPDH",
            "ENO1",
            "ALDOA",
            "PGK1",
            "PFKP",
        ],
        "Mitochondrial OXPHOS": [
            "ATP5",
            "NDUF",
            "COX",
            "UQCR",
            "SDH",
            "MT-CO",
            "MT-ND",
            "CYCS",
        ],
        "DNA repair and replication stress": [
            "BRCA1",
            "BRCA2",
            "RAD51",
            "ATR",
            "ATM",
            "CHEK1",
            "CHEK2",
            "PARP",
            "POLQ",
            "FANCD2",
        ],
        "Hypoxia and stress signalling": [
            "HIF1A",
            "VEGFA",
            "CA9",
            "SLC2A1",
            "BNIP3",
            "DDIT3",
        ],
        "Cell proliferation": [
            "MKI67",
            "PCNA",
            "TOP2A",
            "CDK1",
            "CDK2",
            "CCNB1",
            "AURKA",
            "AURKB",
        ],
        "Antioxidant and redox response": [
            "SOD1",
            "SOD2",
            "CAT",
            "GPX",
            "PRDX",
            "TXN",
            "GSR",
            "NQO1",
        ],
    }

    features = [str(item["feature"]).upper() for item in top_features]

    enriched = []

    for pathway, markers in pathway_map.items():
        matched = []

        for feature in features:
            for marker in markers:
                if marker.upper() in feature:
                    matched.append(feature)

        matched = sorted(set(matched))

        if matched:
            enriched.append(
                {
                    "pathway": pathway,
                    "matched_features": matched,
                    "match_count": len(matched),
                    "interpretation": (
                        f"{pathway} is represented among the highest-ranked features. "
                        "This may indicate altered pathway activity, but it should be validated "
                        "with formal pathway enrichment and biological metadata."
                    ),
                }
            )

    enriched = sorted(enriched, key=lambda x: x["match_count"], reverse=True)

    return enriched


def shap_like_explainability(df: pd.DataFrame):
    """
    Uses permutation importance as a robust explainability method.

    True SHAP can be added later, but permutation importance is more stable
    for small uploaded datasets.
    """
    prepared = prepare_abundance_matrix(df)

    identifiers = prepared["identifiers"]
    log_df = prepared["log_df"]

    X = log_df.T
    X.columns = identifiers.astype(str).values

    control_cols, case_cols = infer_sample_groups(X.index)

    y = []

    for sample in X.index:
        if sample in case_cols:
            y.append(1)
        elif sample in control_cols:
            y.append(0)
        else:
            y.append(0)

    y = np.array(y)

    unique, counts = np.unique(y, return_counts=True)

    if len(unique) < 2 or counts.min() < 2:
        return {
            "warning": (
                "Explainability requires at least two samples per group. "
                "Use labels such as Normal_1, Normal_2, Tumor_1, Tumor_2."
            )
        }

    model = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("classifier", RandomForestClassifier(n_estimators=300, random_state=42)),
        ]
    )

    cv_splits = min(3, int(counts.min()))
    cv = StratifiedKFold(n_splits=cv_splits, shuffle=True, random_state=42)

    scores = cross_val_score(model, X, y, cv=cv, scoring="accuracy")

    model.fit(X, y)

    importance = permutation_importance(
        model,
        X,
        y,
        n_repeats=20,
        random_state=42,
        scoring="accuracy",
    )

    imp_df = pd.DataFrame(
        {
            "feature": X.columns,
            "importance_mean": importance.importances_mean,
            "importance_std": importance.importances_std,
        }
    ).sort_values("importance_mean", ascending=False)

    return {
        "model_accuracy_mean": float(scores.mean()),
        "model_accuracy_std": float(scores.std()),
        "top_explainable_features": imp_df.head(30).to_dict(orient="records"),
    }


def run_advanced_analysis(df: pd.DataFrame):
    differential = differential_abundance(df)

    if "warning" in differential:
        return differential

    volcano_png_base64 = make_volcano_plot_base64(differential["volcano_data"])

    pathway_results = simple_pathway_enrichment(differential["top_biomarkers"])

    explainability = shap_like_explainability(df)

    return {
        "control_samples": differential["control_samples"],
        "case_samples": differential["case_samples"],
        "n_features": differential["n_features"],
        "top_biomarkers": differential["top_biomarkers"],
        "volcano_data": differential["volcano_data"],
        "volcano_png_base64": volcano_png_base64,
        "pathway_enrichment": pathway_results,
        "explainability": explainability,
        "compatibility": {
            "message": (
                "The parser attempts to support simple abundance tables, FragPipe outputs, "
                "and TMT-Integrator-style gene, protein, peptide, and site-level reports."
            )
        },
    }