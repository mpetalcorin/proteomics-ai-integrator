import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from scipy import stats


def clean_numeric_matrix(df: pd.DataFrame):
    """
    Assumes first column contains gene/protein names and the remaining columns are abundance values.
    """
    id_col = df.columns[0]
    numeric_df = df.drop(columns=[id_col]).apply(pd.to_numeric, errors="coerce")

    numeric_df = numeric_df.replace([np.inf, -np.inf], np.nan)

    missing_percent = numeric_df.isna().mean(axis=1) * 100

    numeric_df = numeric_df.fillna(numeric_df.median())

    log_df = np.log2(numeric_df + 1)

    return id_col, df[id_col], numeric_df, log_df, missing_percent


def run_basic_analysis(df: pd.DataFrame):
    id_col, identifiers, numeric_df, log_df, missing_percent = clean_numeric_matrix(df)

    sample_means = log_df.mean(axis=0).round(4).to_dict()
    sample_medians = log_df.median(axis=0).round(4).to_dict()

    pca = PCA(n_components=2)
    pca_values = pca.fit_transform(log_df.T)

    pca_result = []
    for i, sample in enumerate(log_df.columns):
        pca_result.append(
            {
                "sample": sample,
                "pc1": float(pca_values[i, 0]),
                "pc2": float(pca_values[i, 1]),
            }
        )

    explained_variance = {
        "pc1": float(pca.explained_variance_ratio_[0]),
        "pc2": float(pca.explained_variance_ratio_[1]),
    }

    top_variable = log_df.var(axis=1).sort_values(ascending=False).head(20)
    top_variable_features = [
        {
            "feature": str(identifiers.iloc[idx]),
            "variance": float(value),
        }
        for idx, value in top_variable.items()
    ]

    high_missing = [
        {
            "feature": str(identifiers.iloc[i]),
            "missing_percent": float(missing_percent.iloc[i]),
        }
        for i in missing_percent.sort_values(ascending=False).head(20).index
    ]

    return {
        "n_features": int(df.shape[0]),
        "n_samples": int(numeric_df.shape[1]),
        "sample_means": sample_means,
        "sample_medians": sample_medians,
        "pca": pca_result,
        "explained_variance": explained_variance,
        "top_variable_features": top_variable_features,
        "high_missing_features": high_missing,
    }
def run_differential_analysis(df: pd.DataFrame):
    id_col, identifiers, numeric_df, log_df, missing_percent = clean_numeric_matrix(df)

    control_cols = [
        c for c in log_df.columns
        if any(term in c.lower() for term in ["normal", "control", "untreated"])
    ]

    case_cols = [
        c for c in log_df.columns
        if any(term in c.lower() for term in ["tumor", "tumour", "cancer", "treated", "case", "disease"])
    ]

    if len(control_cols) < 2 or len(case_cols) < 2:
        return {
            "warning": "Need at least two control and two case samples. Use sample names such as Normal_1, Normal_2, Tumor_1, Tumor_2."
        }

    results = []

    for i in range(log_df.shape[0]):
        control_values = log_df.loc[log_df.index[i], control_cols].values
        case_values = log_df.loc[log_df.index[i], case_cols].values

        log2fc = float(np.mean(case_values) - np.mean(control_values))

        try:
            t_stat, p_value = stats.ttest_ind(case_values, control_values, equal_var=False)
        except Exception:
            p_value = 1.0

        results.append(
            {
                "feature": str(identifiers.iloc[i]),
                "log2fc": log2fc,
                "p_value": float(p_value),
                "negative_log10_p": float(-np.log10(p_value + 1e-12)),
            }
        )

    results = sorted(results, key=lambda x: x["p_value"])

    return {
        "control_samples": control_cols,
        "case_samples": case_cols,
        "top_differential_features": results[:50],
    }