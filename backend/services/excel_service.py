import pandas as pd
import numpy as np
from typing import Dict, Any
 
NA_STRINGS = {'n/a', 'na', 'none', 'null', '-', '', 'not available', 'no expiry'}
 
 
# ── Dtype Helpers (Pandas 3.0 compatible) ────────────────────────────────────
def is_string_col(series: pd.Series) -> bool:
    return pd.api.types.is_string_dtype(series) or series.dtype == object
 
def is_numeric_col(series: pd.Series) -> bool:
    return pd.api.types.is_numeric_dtype(series)
 
 
# ── Smart Date Parser ─────────────────────────────────────────────────────────
def parse_date_smart(val):
    if not isinstance(val, str) or not val.strip():
        return pd.NaT
    val = val.strip()
    if val.lower() in NA_STRINGS:
        return pd.NaT
    formats = [
        "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y", "%Y/%m/%d",
        "%d.%m.%Y", "%Y.%m.%d", "%d %b %Y", "%b %d, %Y", "%B %d, %Y",
        "%d %B %Y", "%b %d %Y", "%B %d %Y", "%d-%b-%Y", "%Y-%b-%d",
    ]
    for fmt in formats:
        try:
            return pd.to_datetime(val, format=fmt)
        except Exception:
            continue
    try:
        return pd.to_datetime(val, infer_datetime_format=True, errors='coerce')
    except Exception:
        return pd.NaT
 
 
def is_date_column_smart(series: pd.Series) -> bool:
    if not is_string_col(series):
        return False
    cleaned = series.dropna()
    cleaned = cleaned[~cleaned.astype(str).str.strip().str.lower().isin(NA_STRINGS)]
    sample = cleaned.head(10).astype(str)
    if len(sample) == 0:
        return False
    parsed = sum(1 for v in sample if parse_date_smart(v) is not pd.NaT)
    return parsed >= len(sample) * 0.5
 
 
def standardize_date_column(series: pd.Series, target_format: str) -> pd.Series:
    def convert(val):
        if pd.isna(val):
            return val
        s = str(val).strip()
        if s.lower() in NA_STRINGS:
            return val
        parsed = parse_date_smart(s)
        if parsed is pd.NaT:
            return val
        return parsed.strftime(target_format)
    return series.apply(convert)
 
 
def matches(v: str, keywords: list) -> bool:
    return any(k in v for k in keywords)
 
 
def find_column(question_id: str, column_hint: str, df: pd.DataFrame):
    """Find actual column in df matching the hint from Gemini."""
    if column_hint:
        # Exact match first
        if column_hint in df.columns:
            return column_hint
        # Case-insensitive match
        for c in df.columns:
            if c.lower() == column_hint.lower():
                return c
        # Partial match
        for c in df.columns:
            if column_hint.lower() in c.lower() or c.lower() in column_hint.lower():
                return c
    return None
 
 
# ── Main Processing ───────────────────────────────────────────────────────────
def process_dataframe(df: pd.DataFrame, answers: Dict[str, Any], questions: list = None) -> tuple[pd.DataFrame, Dict[str, Any]]:
    stats = {
        "original_rows": len(df),
        "original_columns": len(df.columns),
        "duplicates_removed": 0,
        "missing_handled": {},
        "outliers_removed": 0,
        "columns_cleaned": [],
    }
 
    df = df.copy()
 
    # Build question_id → column map from questions list
    q_column_map = {}
    if questions:
        for q in questions:
            if q.get("column"):
                q_column_map[q["id"]] = q["column"]
 
    for question_id, answer in answers.items():
        values = answer if isinstance(answer, list) else [answer]
 
        # Get column hint for this question
        column_hint = q_column_map.get(question_id)
        target_col = find_column(question_id, column_hint, df) if column_hint else None
 
        for val in values:
            if not isinstance(val, str):
                continue
            v = val.lower().strip()
 
            # ── DUPLICATES ────────────────────────────────────────────
            if v == "remove_duplicates" or matches(v, ["remove_duplicates", "remove duplicate", "remove all dup"]):
                before = len(df)
                df = df.drop_duplicates()
                stats["duplicates_removed"] = before - len(df)
 
            # ── KEEP (skip) ───────────────────────────────────────────
            elif v == "keep":
                pass
 
            # ── MISSING: median ───────────────────────────────────────
            elif v == "fill_median" or matches(v, ["fill_median", "median value", "fill with median", "fill with the median"]):
                cols = [target_col] if target_col and is_numeric_col(df[target_col]) else get_numeric_cols_with_missing(df)
                for c in cols:
                    if df[c].isnull().any():
                        df[c] = df[c].fillna(df[c].median())
                        stats["missing_handled"][c] = "filled with median"
 
            # ── MISSING: mean ─────────────────────────────────────────
            elif v == "fill_mean" or matches(v, ["fill_mean", "mean value", "fill with mean", "fill with the mean"]):
                cols = [target_col] if target_col and is_numeric_col(df[target_col]) else get_numeric_cols_with_missing(df)
                for c in cols:
                    if df[c].isnull().any():
                        df[c] = df[c].fillna(df[c].mean())
                        stats["missing_handled"][c] = "filled with mean"
 
            # ── MISSING: mode ─────────────────────────────────────────
            elif v == "fill_mode" or matches(v, ["fill_mode", "most frequent"]):
                cols = [target_col] if target_col else [c for c in df.columns if is_string_col(df[c]) and df[c].isnull().any()]
                for c in cols:
                    if df[c].isnull().any():
                        mode_val = df[c].mode()
                        df[c] = df[c].fillna(mode_val[0] if len(mode_val) > 0 else "Unknown")
                        stats["missing_handled"][c] = "filled with mode"
 
            # ── MISSING: Unknown ──────────────────────────────────────
            elif v == "fill_unknown" or matches(v, ["fill_unknown", "fill with 'unknown'", "'unknown'"]):
                cols = [target_col] if target_col else [c for c in df.columns if is_string_col(df[c]) and df[c].isnull().any()]
                for c in cols:
                    if is_string_col(df[c]) and df[c].isnull().any():
                        df[c] = df[c].fillna("Unknown")
                        stats["missing_handled"][c] = "filled with Unknown"
 
            # ── MISSING: placeholder / No Expiry ─────────────────────
            elif matches(v, ["9999-12-31", "no expiry", "fill with a placeholder", "far future date", "implies no"]):
                cols = [target_col] if target_col else [c for c in df.columns if is_string_col(df[c]) and is_date_column_smart(df[c]) and df[c].isnull().any()]
                for c in cols:
                    if df[c].isnull().any():
                        df[c] = df[c].fillna("No Expiry")
                        stats["missing_handled"][c] = "filled with No Expiry"
 
            # ── MISSING: fill 0 ───────────────────────────────────────
            elif v == "fill_zero" or matches(v, ["fill_zero", "fill with 0"]):
                cols = [target_col] if target_col and is_numeric_col(df[target_col]) else get_numeric_cols_with_missing(df)
                for c in cols:
                    if df[c].isnull().any():
                        df[c] = df[c].fillna(0)
                        stats["missing_handled"][c] = "filled with 0"
 
            # ── MISSING: drop rows ────────────────────────────────────
            elif v == "drop_rows" or matches(v, ["drop_rows", "remove rows", "drop rows"]):
                before = len(df)
                if target_col:
                    df = df.dropna(subset=[target_col])
                else:
                    df = df.dropna()
                stats["missing_handled"][target_col or "all"] = f"dropped {before - len(df)} rows"
 
            # ── OUTLIERS: cap ─────────────────────────────────────────
            elif v == "cap_outliers" or matches(v, ["cap_outliers", "cap outlier", "nearest non-outlier", "iqr bounds", "cap/floor", "set to boundary", "boundary values"]):
                cols = [target_col] if target_col and is_numeric_col(df[target_col]) else df.select_dtypes(include=[np.number]).columns.tolist()
                for c in cols:
                    Q1 = df[c].quantile(0.25)
                    Q3 = df[c].quantile(0.75)
                    IQR = Q3 - Q1
                    before_col = df[c].copy()
                    df[c] = df[c].clip(lower=Q1 - 1.5 * IQR, upper=Q3 + 1.5 * IQR)
                    if not df[c].equals(before_col) and c not in stats["columns_cleaned"]:
                        stats["columns_cleaned"].append(c)
 
            # ── OUTLIERS: remove ──────────────────────────────────────
            elif v == "remove_outliers" or matches(v, ["remove_outliers", "remove outlier"]):
                cols = [target_col] if target_col and is_numeric_col(df[target_col]) else df.select_dtypes(include=[np.number]).columns.tolist()
                for c in cols:
                    before = len(df)
                    Q1 = df[c].quantile(0.25)
                    Q3 = df[c].quantile(0.75)
                    IQR = Q3 - Q1
                    df = df[~((df[c] < Q1 - 1.5 * IQR) | (df[c] > Q3 + 1.5 * IQR))]
                    stats["outliers_removed"] += before - len(df)
 
            # ── DATE: YYYY-MM-DD ──────────────────────────────────────
            elif v == "yyyy-mm-dd" or matches(v, ["yyyy-mm-dd", "yyyy/mm/dd"]):
                cols = [target_col] if target_col and is_date_column_smart(df[target_col]) else [c for c in df.columns if is_date_column_smart(df[c])]
                for c in cols:
                    df[c] = standardize_date_column(df[c], "%Y-%m-%d")
                    if c not in stats["columns_cleaned"]:
                        stats["columns_cleaned"].append(c)
 
            # ── DATE: DD/MM/YYYY ──────────────────────────────────────
            elif v == "dd/mm/yyyy" or matches(v, ["dd/mm/yyyy", "dd-mm-yyyy"]):
                cols = [target_col] if target_col and is_date_column_smart(df[target_col]) else [c for c in df.columns if is_date_column_smart(df[c])]
                for c in cols:
                    df[c] = standardize_date_column(df[c], "%d/%m/%Y")
                    if c not in stats["columns_cleaned"]:
                        stats["columns_cleaned"].append(c)
 
            # ── CASING: Title Case ────────────────────────────────────
            elif v == "title_case" or matches(v, ["title_case", "title case"]):
                cols = [target_col] if target_col else [c for c in df.columns if is_string_col(df[c]) and not is_date_column_smart(df[c])]
                for c in cols:
                    if is_string_col(df[c]) and not is_date_column_smart(df[c]):
                        df[c] = df[c].apply(lambda x: x.strip().title() if isinstance(x, str) else x)
                        if c not in stats["columns_cleaned"]:
                            stats["columns_cleaned"].append(c)
 
            # ── CASING: UPPER ─────────────────────────────────────────
            elif v == "upper_case" or matches(v, ["upper_case", "upper case", "uppercase"]):
                cols = [target_col] if target_col else [c for c in df.columns if is_string_col(df[c]) and not is_date_column_smart(df[c])]
                for c in cols:
                    if is_string_col(df[c]) and not is_date_column_smart(df[c]):
                        df[c] = df[c].apply(lambda x: x.strip().upper() if isinstance(x, str) else x)
                        if c not in stats["columns_cleaned"]:
                            stats["columns_cleaned"].append(c)
 
            # ── CASING: lower ─────────────────────────────────────────
            elif v == "lower_case" or matches(v, ["lower_case", "lower case", "lowercase"]):
                cols = [target_col] if target_col else [c for c in df.columns if is_string_col(df[c]) and not is_date_column_smart(df[c])]
                for c in cols:
                    if is_string_col(df[c]) and not is_date_column_smart(df[c]):
                        df[c] = df[c].apply(lambda x: x.strip().lower() if isinstance(x, str) else x)
                        if c not in stats["columns_cleaned"]:
                            stats["columns_cleaned"].append(c)
 
    # Always clean column names
    df.columns = [str(c).strip().replace(" ", "_") for c in df.columns]
 
    stats["final_rows"] = len(df)
    stats["final_columns"] = len(df.columns)
    stats["rows_removed"] = stats["original_rows"] - stats["final_rows"]
 
    return df, stats
 
 
def get_numeric_cols_with_missing(df):
    return [c for c in df.columns if is_numeric_col(df[c]) and df[c].isnull().any()]
 
def get_text_cols_with_missing(df):
    return [c for c in df.columns if is_string_col(df[c]) and df[c].isnull().any()]
