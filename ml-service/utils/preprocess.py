import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, MultiLabelBinarizer, StandardScaler


def _as_dense(matrix):
    """
    Handle both sparse and dense sklearn outputs safely.
    """
    return matrix.toarray() if hasattr(matrix, "toarray") else np.asarray(matrix)


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    # Standardize text columns; noisy CSVs usually contain mixed casing and blanks.
    text_cols = ["education_level", "degree_stream", "location", "risk_preference"]
    for col in text_cols:
        if col in df.columns:
            df[col] = (
                df[col]
                .fillna("unknown")
                .astype(str)
                .str.strip()
                .str.lower()
            )

    if "skills" in df.columns:
        df["skills"] = df["skills"].fillna("").apply(
            lambda s: [x.strip().lower() for x in str(s).split(",") if x.strip()]
        )

    if "interests" in df.columns:
        df["interests"] = df["interests"].fillna("").apply(
            lambda s: [x.strip().lower() for x in str(s).split(",") if x.strip()]
        )

    numeric_cols = ["years_experience", "salary"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df[col] = df[col].fillna(df[col].median() if not np.isnan(df[col].median()) else 0)

    return df


def build_feature_matrix(df: pd.DataFrame):
    categorical_cols = ["education_level", "degree_stream", "location", "risk_preference"]
    numeric_cols = ["years_experience", "skills_count"]

    matrix_df = df.copy()
    matrix_df["skills_count"] = matrix_df["skills"].apply(len)
    matrix_df["interests_count"] = matrix_df["interests"].apply(len)

    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_cols),
            ("num", StandardScaler(), numeric_cols),
        ],
        remainder="drop",
    )

    X_base = preprocessor.fit_transform(matrix_df)

    mlb_skills = MultiLabelBinarizer()
    X_skills = mlb_skills.fit_transform(matrix_df["skills"])

    mlb_interests = MultiLabelBinarizer()
    X_interests = mlb_interests.fit_transform(matrix_df["interests"])

    X = np.hstack([_as_dense(X_base), X_skills, X_interests])
    return X, preprocessor, mlb_skills, mlb_interests


def transform_single_input(payload: dict, preprocessor, mlb_skills, mlb_interests):
    one = pd.DataFrame(
        [
            {
                "education_level": payload["educationLevel"].strip().lower(),
                "degree_stream": payload["degreeStream"].strip().lower(),
                "location": payload["location"].strip().lower(),
                "risk_preference": payload["riskPreference"].strip().lower(),
                "years_experience": payload.get("yearsExperience", 0),
                "skills_count": len(payload.get("skills", [])),
                "interests_count": len(payload.get("interests", [])),
            }
        ]
    )

    one_base = _as_dense(preprocessor.transform(one))
    one_skills = mlb_skills.transform(
        [[s.strip().lower() for s in payload.get("skills", []) if s.strip()]]
    )
    one_interests = mlb_interests.transform(
        [[i.strip().lower() for i in payload.get("interests", []) if i.strip()]]
    )

    return np.hstack([one_base, one_skills, one_interests])
