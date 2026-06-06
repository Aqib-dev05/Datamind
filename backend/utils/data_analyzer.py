import pandas as pd
import numpy as np
import math
from typing import Dict, List, Any
 
 
def clean_value(val):
    """Convert NaN/inf to None for JSON safety."""
    if val is None:
        return None
    try:
        if math.isnan(val) or math.isinf(val):
            return None
    except (TypeError, ValueError):
        pass
    return val
 
 
def analyze_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
    analysis = {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "columns": [],
        "duplicate_rows": int(df.duplicated().sum()),
        "total_missing": int(df.isnull().sum().sum()),
    }
 
    for col in df.columns:
        missing_count = int(df[col].isnull().sum())
        missing_pct = clean_value(round(float(df[col].isnull().mean() * 100), 2)) or 0.0
 
        col_info = {
            "name": col,
            "dtype": str(df[col].dtype),
            "missing_count": missing_count,
            "missing_pct": missing_pct,
            "unique_count": int(df[col].nunique()),
            "sample_values": df[col].dropna().head(3).astype(str).tolist(),
        }
 
        if pd.api.types.is_numeric_dtype(df[col]):
            col_info["type_category"] = "numeric"
            mean_val = df[col].mean() if not df[col].isnull().all() else None
            col_info["mean"] = clean_value(round(float(mean_val), 2)) if mean_val is not None else None
            col_info["outlier_count"] = count_outliers(df[col])
        elif is_date_column(df[col]):
            col_info["type_category"] = "date"
        else:
            col_info["type_category"] = "text"
 
        analysis["columns"].append(col_info)
 
    return analysis
 
 
def count_outliers(series: pd.Series) -> int:
    series = series.dropna()
    if len(series) < 4:
        return 0
    Q1 = series.quantile(0.25)
    Q3 = series.quantile(0.75)
    IQR = Q3 - Q1
    outliers = series[(series < Q1 - 1.5 * IQR) | (series > Q3 + 1.5 * IQR)]
    return int(len(outliers))
 
 
def is_date_column(series: pd.Series) -> bool:
    sample = series.dropna().head(10).astype(str)
    date_patterns = ["2020", "2021", "2022", "2023", "2024", "2025", "/", "-"]
    matches = sum(1 for val in sample if any(p in val for p in date_patterns))
    return matches >= len(sample) * 0.6
 
 
def get_preview(df: pd.DataFrame, rows: int = 5) -> List[Dict[str, Any]]:
    preview_df = df.head(rows).copy()
    # Replace all NaN/inf with None
    preview_df = preview_df.where(pd.notnull(preview_df), None)
    records = preview_df.to_dict(orient="records")
    # Extra safety pass
    cleaned = []
    for record in records:
        clean_record = {}
        for k, v in record.items():
            if isinstance(v, float):
                clean_record[k] = clean_value(v)
            else:
                clean_record[k] = v
        cleaned.append(clean_record)
    return cleaned
