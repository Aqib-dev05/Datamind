import pandas as pd
import numpy as np
from typing import Dict, Any
 
 
def process_dataframe(df: pd.DataFrame, answers: Dict[str, Any]) -> tuple[pd.DataFrame, Dict[str, Any]]:
    stats = {
        "original_rows": len(df),
        "original_columns": len(df.columns),
        "duplicates_removed": 0,
        "missing_handled": {},
        "outliers_removed": 0,
        "columns_cleaned": [],
    }
 
    df = df.copy()
 
    # Extract column names mentioned in question text from Gemini
    # answers = { "q1": "some value", "q2": ["val1", "val2"] }
 
    for question_id, answer in answers.items():
        values = answer if isinstance(answer, list) else [answer]
 
        for val in values:
            if not isinstance(val, str):
                continue
            v = val.lower().strip()
 
            # ── DUPLICATES ───────────────────────────────────────────
            if "remove duplicate" in v or (("remove" in v or "drop" in v) and "dup" in question_id.lower()):
                before = len(df)
                df = df.drop_duplicates()
                stats["duplicates_removed"] = before - len(df)
 
            # ── MISSING: fill mean ───────────────────────────────────
            elif "mean" in v and "fill" in v:
                cols = get_numeric_cols_with_missing(df)
                for c in cols:
                    df[c] = df[c].fillna(df[c].mean())
                    stats["missing_handled"][c] = "filled with mean"
 
            # ── MISSING: fill median ─────────────────────────────────
            elif "median" in v:
                cols = get_numeric_cols_with_missing(df)
                for c in cols:
                    df[c] = df[c].fillna(df[c].median())
                    stats["missing_handled"][c] = "filled with median"
 
            # ── MISSING: fill mode / most frequent ──────────────────
            elif "mode" in v or "most frequent" in v:
                cols = get_text_cols_with_missing(df)
                for c in cols:
                    mode_val = df[c].mode()
                    df[c] = df[c].fillna(mode_val[0] if len(mode_val) > 0 else "Unknown")
                    stats["missing_handled"][c] = "filled with mode"
 
            # ── MISSING: fill Unknown ────────────────────────────────
            elif "unknown" in v or "fill with 'unknown'" in v:
                cols = get_text_cols_with_missing(df)
                for c in cols:
                    df[c] = df[c].fillna("Unknown")
                    stats["missing_handled"][c] = "filled with Unknown"
 
            # ── MISSING: fill 0 / specific value ────────────────────
            elif ("specific value" in v or "fill with 0" in v or "fill with a specific" in v):
                cols = get_numeric_cols_with_missing(df)
                for c in cols:
                    df[c] = df[c].fillna(0)
                    stats["missing_handled"][c] = "filled with 0"
 
            # ── MISSING: remove rows ─────────────────────────────────
            elif "remove rows" in v or "remove the rows" in v:
                before = len(df)
                df = df.dropna()
                removed = before - len(df)
                stats["missing_handled"]["all_columns"] = f"dropped {removed} rows with missing values"
 
            # ── OUTLIERS: remove rows ────────────────────────────────
            elif "remove" in v and "outlier" in v:
                cols = df.select_dtypes(include=[np.number]).columns.tolist()
                for c in cols:
                    before = len(df)
                    Q1 = df[c].quantile(0.25)
                    Q3 = df[c].quantile(0.75)
                    IQR = Q3 - Q1
                    df = df[~((df[c] < Q1 - 1.5 * IQR) | (df[c] > Q3 + 1.5 * IQR))]
                    stats["outliers_removed"] += before - len(df)
 
            # ── OUTLIERS: cap ────────────────────────────────────────
            elif "cap" in v or "floor" in v or "cap/floor" in v:
                cols = df.select_dtypes(include=[np.number]).columns.tolist()
                for c in cols:
                    Q1 = df[c].quantile(0.25)
                    Q3 = df[c].quantile(0.75)
                    IQR = Q3 - Q1
                    df[c] = df[c].clip(lower=Q1 - 1.5 * IQR, upper=Q3 + 1.5 * IQR)
                    if c not in stats["columns_cleaned"]:
                        stats["columns_cleaned"].append(c)
 
            # ── DATE: YYYY-MM-DD ─────────────────────────────────────
            elif "yyyy-mm-dd" in v:
                for c in df.columns:
                    if df[c].dtype == object:
                        try:
                            converted = pd.to_datetime(df[c], infer_datetime_format=True, errors="coerce")
                            if converted.notna().sum() > len(df) * 0.4:
                                df[c] = converted.dt.strftime("%Y-%m-%d")
                                if c not in stats["columns_cleaned"]:
                                    stats["columns_cleaned"].append(c)
                        except Exception:
                            pass
 
            # ── DATE: YYYY-MM-DD ─────────────────────────────────────────────
            elif "yyyy-mm-dd" in v.lower():
                for c in df.columns:
                    if df[c].dtype == object:
                        try:
                            converted = pd.to_datetime(df[c], dayfirst=False, errors="coerce")
                            # Try dayfirst=True if too many NaT
                            if converted.isna().sum() > len(df) * 0.3:
                                converted = pd.to_datetime(df[c], dayfirst=True, errors="coerce")
                            if converted.notna().sum() > len(df) * 0.4:
                                df[c] = converted.dt.strftime("%Y-%m-%d")
                                if c not in stats["columns_cleaned"]:
                                    stats["columns_cleaned"].append(c)
                        except Exception:
                            pass
 
            # ── CASING: Title Case ───────────────────────────────────
            elif "title case" in v or "title_case" in v:
                for c in df.select_dtypes(include="object").columns:
                    df[c] = df[c].apply(lambda x: x.strip().title() if isinstance(x, str) else x)
                    if c not in stats["columns_cleaned"]:
                        stats["columns_cleaned"].append(c)
 
            # ── CASING: Uppercase ────────────────────────────────────
            elif "uppercase" in v or "upper case" in v:
                for c in df.select_dtypes(include="object").columns:
                    df[c] = df[c].apply(lambda x: x.strip().upper() if isinstance(x, str) else x)
                    if c not in stats["columns_cleaned"]:
                        stats["columns_cleaned"].append(c)
 
            # ── CASING: Lowercase ────────────────────────────────────
            elif "lowercase" in v or "lower case" in v:
                for c in df.select_dtypes(include="object").columns:
                    df[c] = df[c].apply(lambda x: x.strip().lower() if isinstance(x, str) else x)
                    if c not in stats["columns_cleaned"]:
                        stats["columns_cleaned"].append(c)
 
            # ── Convert to integer ───────────────────────────────────
            elif "integer" in v or "convert" in v and "int" in v:
                for c in df.select_dtypes(include=[np.number]).columns:
                    try:
                        df[c] = df[c].fillna(0).astype(int)
                        if c not in stats["columns_cleaned"]:
                            stats["columns_cleaned"].append(c)
                    except Exception:
                        pass
 
    # Always clean column names
    df.columns = [str(c).strip().replace(" ", "_") for c in df.columns]
 
    stats["final_rows"] = len(df)
    stats["final_columns"] = len(df.columns)
    stats["rows_removed"] = stats["original_rows"] - stats["final_rows"]
 
    return df, stats
 
 
def get_numeric_cols_with_missing(df: pd.DataFrame):
    return [c for c in df.select_dtypes(include=[np.number]).columns if df[c].isnull().any()]
 
 
def get_text_cols_with_missing(df: pd.DataFrame):
    return [c for c in df.select_dtypes(include="object").columns if df[c].isnull().any()]
