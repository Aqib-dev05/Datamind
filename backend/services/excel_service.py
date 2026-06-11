import pandas as pd
import numpy as np
from typing import Dict, Any
 
NA_STRINGS = {'n/a', 'na', 'none', 'null', '-', '', 'not available', 'no expiry'}
 
 
# ── Dtype Helpers (Pandas 3.0 compatible) ────────────────────────────────────
def is_string_col(series: pd.Series) -> bool:
    """Works for both old object dtype and new pandas 3.0 str dtype."""
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
        "%Y-%m-%d",   "%d/%m/%Y",   "%d-%m-%Y",
        "%m/%d/%Y",   "%Y/%m/%d",   "%d.%m.%Y",
        "%Y.%m.%d",   "%d %b %Y",   "%b %d, %Y",
        "%B %d, %Y",  "%d %B %Y",   "%b %d %Y",
        "%B %d %Y",   "%d-%b-%Y",   "%Y-%b-%d",
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
 
 
# ── Keyword Matching ──────────────────────────────────────────────────────────
def matches(v: str, keywords: list) -> bool:
    return any(k in v for k in keywords)
 
 
# ── Main Processing ───────────────────────────────────────────────────────────
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
 
    for question_id, answer in answers.items():
        values = answer if isinstance(answer, list) else [answer]
 
        for val in values:
            if not isinstance(val, str):
                continue
            v = val.lower().strip()
 
            # ── DUPLICATES ────────────────────────────────────────────
            if matches(v, ["remove_duplicates", "remove duplicate", "remove all dup", "drop dup"]) or \
               (matches(v, ["remove", "drop"]) and "dup" in question_id.lower()):
                before = len(df)
                df = df.drop_duplicates()
                stats["duplicates_removed"] = before - len(df)
 
            # ── MISSING: median ───────────────────────────────────────
            elif matches(v, ["median value", "fill with the median", "fill with median", "fill_median", "impute median"]):
                for c in get_numeric_cols_with_missing(df):
                    df[c] = df[c].fillna(df[c].median())
                    stats["missing_handled"][c] = "filled with median"
 
            # ── MISSING: mean ─────────────────────────────────────────
            elif matches(v, ["mean value", "fill with the mean", "fill with mean", "fill_mean", "impute mean"]):
                for c in get_numeric_cols_with_missing(df):
                    df[c] = df[c].fillna(df[c].mean())
                    stats["missing_handled"][c] = "filled with mean"
 
            # ── MISSING: mode ─────────────────────────────────────────
            elif matches(v, ["fill_mode", "most frequent", "mode value"]):
                for c in df.columns:
                    if is_string_col(df[c]) and df[c].isnull().any():
                        mode_val = df[c].mode()
                        df[c] = df[c].fillna(mode_val[0] if len(mode_val) > 0 else "Unknown")
                        stats["missing_handled"][c] = "filled with mode"
 
            # ── MISSING: placeholder (No Expiry / 9999) ───────────────
            elif matches(v, ["9999-12-31", "no expiry", "fill with a placeholder", "placeholder", "far future date", "implies no"]):
             for c in df.columns:
                  if is_string_col(df[c]) and df[c].isnull().any() and is_date_column_smart(df[c]):
                     df[c] = df[c].fillna("No Expiry")
                     stats["missing_handled"][c] = "filled with No Expiry"
 
            # ── MISSING: Unknown ──────────────────────────────────────
            elif matches(v, ["fill_unknown", "fill with 'unknown'", "'unknown'", "unknown"]) and \
                 not matches(v, ["no expiry", "placeholder", "9999"]):
                for c in df.columns:
                    if is_string_col(df[c]) and df[c].isnull().any():
                        df[c] = df[c].fillna("Unknown")
                        stats["missing_handled"][c] = "filled with Unknown"
 
            # ── MISSING: fill 0 ───────────────────────────────────────
            elif matches(v, ["fill_zero", "fill with 0", "fill with zero"]):
                for c in get_numeric_cols_with_missing(df):
                    df[c] = df[c].fillna(0)
                    stats["missing_handled"][c] = "filled with 0"
 
            # ── MISSING: drop rows ────────────────────────────────────
            elif matches(v, ["drop_rows", "remove rows", "remove the rows", "delete rows", "drop rows"]):
                before = len(df)
                df = df.dropna()
                stats["missing_handled"]["all"] = f"dropped {before - len(df)} rows"
 
            # ── OUTLIERS: keep ────────────────────────────────────────
            elif matches(v, ["keep outlier", "keep them", "keep as"]) and "outlier" in v:
                pass
 
            # ── OUTLIERS: remove ──────────────────────────────────────
            elif matches(v, ["remove_outliers", "remove outlier", "delete outlier"]):
                for c in df.select_dtypes(include=[np.number]).columns:
                    before = len(df)
                    Q1 = df[c].quantile(0.25)
                    Q3 = df[c].quantile(0.75)
                    IQR = Q3 - Q1
                    df = df[~((df[c] < Q1 - 1.5 * IQR) | (df[c] > Q3 + 1.5 * IQR))]
                    stats["outliers_removed"] += before - len(df)
 
            # ── OUTLIERS: cap ─────────────────────────────────────────
            elif matches(v, ["cap outlier", "cap_outlier", "cap/floor", "nearest non-outlier", "cap to", "cap them", "iqr bounds", "iqr"]):
                for c in df.select_dtypes(include=[np.number]).columns:
                    Q1 = df[c].quantile(0.25)
                    Q3 = df[c].quantile(0.75)
                    IQR = Q3 - Q1
                    before_col = df[c].copy()
                    df[c] = df[c].clip(lower=Q1 - 1.5 * IQR, upper=Q3 + 1.5 * IQR)
                    if not df[c].equals(before_col) and c not in stats["columns_cleaned"]:
                        stats["columns_cleaned"].append(c)
 
            # ── DATE: YYYY-MM-DD ──────────────────────────────────────
            elif matches(v, ["yyyy-mm-dd", "yyyy/mm/dd"]) or \
                 (matches(v, ["standardize"]) and matches(v, ["yyyy", "2024-01"])):
                for c in df.columns:
                    if is_date_column_smart(df[c]):
                        df[c] = standardize_date_column(df[c], "%Y-%m-%d")
                        if c not in stats["columns_cleaned"]:
                            stats["columns_cleaned"].append(c)
 
            # ── DATE: DD/MM/YYYY ──────────────────────────────────────
            elif matches(v, ["dd/mm/yyyy", "dd-mm-yyyy", "10/01/2024", "10/01"]) or \
                 (matches(v, ["standardize"]) and matches(v, ["dd/", "dd-", "/mm/"])):
                for c in df.columns:
                    if is_date_column_smart(df[c]):
                        df[c] = standardize_date_column(df[c], "%d/%m/%Y")
                        if c not in stats["columns_cleaned"]:
                            stats["columns_cleaned"].append(c)
 
            # ── CASING: Title Case ────────────────────────────────────
            elif matches(v, ["title_case", "title case", "proper case"]):
                for c in df.columns:
                    if is_string_col(df[c]) and not is_date_column_smart(df[c]):
                        df[c] = df[c].apply(lambda x: x.strip().title() if isinstance(x, str) else x)
                        if c not in stats["columns_cleaned"]:
                            stats["columns_cleaned"].append(c)
 
            # ── CASING: UPPER ─────────────────────────────────────────
            elif matches(v, ["upper_case", "upper case", "uppercase", "to uppercase", "convert to uppercase"]):
                for c in df.columns:
                    if is_string_col(df[c]) and not is_date_column_smart(df[c]):
                        df[c] = df[c].apply(lambda x: x.strip().upper() if isinstance(x, str) else x)
                        if c not in stats["columns_cleaned"]:
                            stats["columns_cleaned"].append(c)
 
            # ── CASING: lower ─────────────────────────────────────────
            elif matches(v, ["lower_case", "lower case", "lowercase", "to lowercase"]):
                for c in df.columns:
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
