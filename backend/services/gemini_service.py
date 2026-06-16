import google.generativeai as genai
import json
import re
import itertools
import os
from typing import Dict, Any, List
 
API_KEYS = [k for k in [
    os.getenv("GEMINI_KEY_1"),
    os.getenv("GEMINI_KEY_2"),
    os.getenv("GEMINI_KEY_3"),
    os.getenv("GEMINI_KEY_4"),
] if k]
 
MODELS = [
    "gemini-2.0-flash",
    "gemini-2.5-flash",
]
 
COMBINATIONS = [(key, model) for key in API_KEYS for model in MODELS]
combo_cycle = itertools.cycle(COMBINATIONS)
current_combo = next(combo_cycle)
 
 
def get_model():
    key, model_name = current_combo
    genai.configure(api_key=key)
    return genai.GenerativeModel(model_name)
 
 
def generate_with_fallback(prompt: str) -> str:
    global current_combo
    tried = 0
    last_error = None
    while tried < len(COMBINATIONS):
        try:
            model = get_model()
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower():
                current_combo = next(combo_cycle)
                tried += 1
                key, mdl = current_combo
                print(f"[Rotation] Switched to model={mdl}, key=...{key[-6:]}")
                last_error = e
            else:
                raise e
    raise Exception(f"All API key+model combinations exhausted. Last error: {last_error}")
 
 
# ── Question Generation ──────────────────────────────────────────────────────
def generate_questions(analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
    try:
        prompt = f"""
You are a data analyst AI. Analyze this Excel/CSV file and generate smart cleaning questions for the user.
 
FILE ANALYSIS:
- Total Rows: {analysis['total_rows']}
- Total Columns: {analysis['total_columns']}
- Duplicate Rows: {analysis['duplicate_rows']}
- Total Missing Values: {analysis['total_missing']}
- Columns: {json.dumps(analysis['columns'], indent=2)}
 
STRICT RULES FOR QUESTION GENERATION:
1. For DUPLICATES: one question if duplicate_rows > 0
2. For MISSING VALUES: one question per column that has missing values (mention exact column name and count)
3. For OUTLIERS: one question per numeric column that has outliers (mention exact column name)
4. For DATE FORMAT: one question per date column (mention exact column name)
5. For TEXT CASING: one question PER TEXT COLUMN separately - do NOT group columns together. Each text column gets its own casing question.
6. Do NOT combine multiple columns into one question
7. Generate maximum 12 questions total
 
Return ONLY a JSON array (no markdown, no explanation):
[
  {{
    "id": "q1",
    "question": "Question text mentioning the specific column name",
    "type": "radio",
    "column": "exact_column_name",
    "options": [
      {{"id": "o1", "label": "Option label", "value": "option_value"}},
      {{"id": "o2", "label": "Option label", "value": "option_value"}}
    ]
  }}
]
 
For text casing questions, options values must be exactly one of: title_case, upper_case, lower_case, keep
For date questions, option values must be exactly one of: yyyy-mm-dd, dd/mm/yyyy, keep
For missing value questions, option values must be exactly one of: fill_mean, fill_median, fill_mode, fill_unknown, fill_zero, drop_rows, keep
For duplicate questions, option values must be exactly one of: remove_duplicates, keep
For outlier questions, option values must be exactly one of: remove_outliers, cap_outliers, keep
"""
        text = generate_with_fallback(prompt)
        text = re.sub(r"```json|```", "", text).strip()
        questions = json.loads(text)
        return questions
    except Exception as e:
        print(f"[Gemini] Question generation failed: {e}")
        return get_fallback_questions(analysis)
 
 
# ── Summary Generation ───────────────────────────────────────────────────────
def generate_summary(stats: Dict[str, Any]) -> str:
    try:
        prompt = f"""
You are a data analyst. Write a short, clear, friendly summary (3-5 sentences) of what was done to clean this data.
Stats: {json.dumps(stats)}
Be specific about numbers. Mention what was removed, fixed, or kept. End with a positive note.
Return only the summary text, no markdown.
"""
        return generate_with_fallback(prompt)
    except Exception as e:
        print(f"[Gemini] Summary generation failed: {e}")
        rows_removed = stats.get('rows_removed', 0)
        duplicates = stats.get('duplicates_removed', 0)
        missing = stats.get('missing_handled', {})
        cleaned = stats.get('columns_cleaned', [])
        return (
            f"Data cleaning complete! Started with {stats.get('original_rows')} rows, "
            f"ended with {stats.get('final_rows')} rows. "
            f"Removed {duplicates} duplicate row(s). "
            f"Handled missing values in {len(missing)} column(s). "
            f"{'Cleaned formatting in ' + str(len(cleaned)) + ' column(s). ' if cleaned else ''}"
            f"Your file is ready to download."
        )
 
 
# ── Fallback Questions ───────────────────────────────────────────────────────
def get_fallback_questions(analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
    questions = []
    q_num = 1
 
    # Duplicates
    if analysis["duplicate_rows"] > 0:
        questions.append({
            "id": f"q{q_num}", "question": f"Found {analysis['duplicate_rows']} duplicate rows. What should we do?",
            "type": "radio", "column": None,
            "options": [
                {"id": "o1", "label": "Remove all duplicates", "value": "remove_duplicates"},
                {"id": "o2", "label": "Keep duplicates as-is", "value": "keep"},
            ]
        })
        q_num += 1
 
    # Missing values — per column
    for col in analysis["columns"]:
        if col["missing_count"] > 0:
            if col["type_category"] == "numeric":
                options = [
                    {"id": "o1", "label": "Fill with mean", "value": "fill_mean"},
                    {"id": "o2", "label": "Fill with median", "value": "fill_median"},
                    {"id": "o3", "label": "Fill with 0", "value": "fill_zero"},
                    {"id": "o4", "label": "Remove rows with missing values", "value": "drop_rows"},
                ]
            else:
                options = [
                    {"id": "o1", "label": "Fill with 'Unknown'", "value": "fill_unknown"},
                    {"id": "o2", "label": "Fill with most frequent value", "value": "fill_mode"},
                    {"id": "o3", "label": "Remove rows with missing values", "value": "drop_rows"},
                    {"id": "o4", "label": "Keep as-is", "value": "keep"},
                ]
            questions.append({
                "id": f"q{q_num}",
                "question": f"Column '{col['name']}' has {col['missing_count']} missing values. How to handle?",
                "type": "radio", "column": col["name"], "options": options
            })
            q_num += 1
 
    # Outliers — per numeric column
    for col in analysis["columns"]:
        if col.get("outlier_count", 0) > 0:
            questions.append({
                "id": f"q{q_num}",
                "question": f"Column '{col['name']}' has {col['outlier_count']} outlier(s). How to handle?",
                "type": "radio", "column": col["name"],
                "options": [
                    {"id": "o1", "label": "Cap outliers to IQR bounds", "value": "cap_outliers"},
                    {"id": "o2", "label": "Remove rows with outliers", "value": "remove_outliers"},
                    {"id": "o3", "label": "Keep outliers as-is", "value": "keep"},
                ]
            })
            q_num += 1
 
    # Date format — per date column
    for col in analysis["columns"]:
        if col["type_category"] == "date":
            questions.append({
                "id": f"q{q_num}",
                "question": f"Column '{col['name']}' has mixed date formats. Standardize to?",
                "type": "radio", "column": col["name"],
                "options": [
                    {"id": "o1", "label": "YYYY-MM-DD (e.g., 2024-01-15)", "value": "yyyy-mm-dd"},
                    {"id": "o2", "label": "DD/MM/YYYY (e.g., 15/01/2024)", "value": "dd/mm/yyyy"},
                    {"id": "o3", "label": "Keep existing formats", "value": "keep"},
                ]
            })
            q_num += 1
 
    # Text casing — per text column separately
    for col in analysis["columns"]:
        if col["type_category"] == "text":
            questions.append({
                "id": f"q{q_num}",
                "question": f"Column '{col['name']}' has inconsistent casing (e.g., {', '.join(col['sample_values'][:2])}). Standardize to?",
                "type": "radio", "column": col["name"],
                "options": [
                    {"id": "o1", "label": "Title Case (e.g., Ahmed Khan)", "value": "title_case"},
                    {"id": "o2", "label": "UPPER CASE", "value": "upper_case"},
                    {"id": "o3", "label": "lower case", "value": "lower_case"},
                    {"id": "o4", "label": "Keep existing casing", "value": "keep"},
                ]
            })
            q_num += 1
 
    return questions
