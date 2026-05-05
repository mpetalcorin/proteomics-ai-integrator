import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline


def prepare_ml_data(df: pd.DataFrame):
    """
    Expected format:
    first column = protein/gene identifier
    remaining columns = sample abundance values

    This function transposes the data so that:
    rows = samples
    columns = proteins/features
    """
    id_col = df.columns[0]
    numeric_df = df.drop(columns=[id_col]).apply(pd.to_numeric, errors="coerce")
    numeric_df = numeric_df.replace([np.inf, -np.inf], np.nan)
    numeric_df = numeric_df.fillna(numeric_df.median())
    log_df = np.log2(numeric_df + 1)

    X = log_df.T
    X.columns = df[id_col].astype(str).values

    return X


def infer_labels_from_sample_names(sample_names):
    """
    Simple automatic label inference.
    If sample names contain tumor, cancer, treated, or case, label = 1.
    Otherwise label = 0.
    """
    labels = []
    for name in sample_names:
        n = str(name).lower()
        if any(term in n for term in ["tumor", "tumour", "cancer", "treated", "case", "disease"]):
            labels.append(1)
        else:
            labels.append(0)
    return np.array(labels)


def run_ml_prediction(df: pd.DataFrame):
    X = prepare_ml_data(df)
    y = infer_labels_from_sample_names(X.index)

    if len(set(y)) < 2:
        return {
            "warning": "Could not infer two biological groups from sample names. Rename samples using terms such as Tumor, Normal, Treated, Control, Case, or Disease.",
            "n_samples": int(X.shape[0]),
            "n_features": int(X.shape[1]),
        }

    n_components = min(10, X.shape[0] - 1, X.shape[1])

    model = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("pca", PCA(n_components=n_components)),
            ("classifier", RandomForestClassifier(n_estimators=300, random_state=42)),
        ]
    )

    scores = cross_val_score(model, X, y, cv=min(3, len(y)), scoring="accuracy")

    model.fit(X, y)

    classifier = model.named_steps["classifier"]
    pca = model.named_steps["pca"]

    importances = classifier.feature_importances_

    top_components = [
        {
            "component": f"PC{i + 1}",
            "importance": float(importances[i]),
        }
        for i in np.argsort(importances)[::-1][:10]
    ]

    return {
        "n_samples": int(X.shape[0]),
        "n_features": int(X.shape[1]),
        "inferred_labels": {
            str(sample): int(label)
            for sample, label in zip(X.index, y)
        },
        "cross_validated_accuracy_mean": float(scores.mean()),
        "cross_validated_accuracy_std": float(scores.std()),
        "top_predictive_components": top_components,
        "interpretation": "The model uses the protein abundance pattern to predict whether a sample belongs to the inferred disease or control group.",
    }