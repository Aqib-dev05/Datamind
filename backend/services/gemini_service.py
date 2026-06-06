import google.generativeai as genai
import json
import re
from config import GEMINI_API_KEY
from typing import Dict, Any, List
 
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")
 
 
def generate_questions(analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
    try:
        prompt = f"""
You are a data analyst AI. Analyze this Excel/CSV file analysis and generate smart questions to ask the user before cleaning/processing.
 
FILE ANALYSIS:
- Total Rows: {analysis['total_rows']}
- Total Columns: {analysis['total_columns']}
- Duplicate Rows: {analysis['duplicate_rows']}
- Total Missing Values: {analysis['total_missing']}
- Columns: {json.dumps(analysis['columns'], indent=2)}
 
Generate 4-8 relevant questions based on what you find in the data. Each question should be actionable.
 
Return ONLY a JSON array with this exact structure (no markdown, no explanation):
[
  {{
    "id": "q1",
    "question": "Question text here",
    "type": "radio",
    "column": "column_name or null",
    "options": [
      {{"id": "o1", "label": "Option label", "value": "option_value"}},
      {{"id": "o2", "label": "Option label", "value": "option_value"}}
    ]
  }}
]
 
Rules:
- type must be "checkbox" (multi-select) or "radio" (single-select)
- Always include a question about duplicate rows if duplicates > 0
- Always include questions about missing value handling for columns with missing data
- Include outlier handling for numeric columns with outliers
- Include date format standardization if date columns exist
- Include text casing standardization if text columns exist
- Make questions specific, mentioning actual column names and counts
- options must always have at least 2 choices
- option values must be simple lowercase keywords like: remove_duplicates, fill_mean, fill_median, fill_unknown, drop_rows, yyyy-mm-dd, dd/mm/yyyy, title_case, upper_case, lower_case, remove_outliers, cap_outliers, keep
"""
        response = model.generate_content(prompt)
        text = response.text.strip()
        text = re.sub(r"```json|```", "", text).strip()
        questions = json.loads(text)
        return questions
    except Exception as e:
        print(f"Gemini question generation failed: {e}")
        return get_fallback_questions(analysis)
 
 
def get_fallback_questions(analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
    questions = []
 
    if analysis["duplicate_rows"] > 0:
        questions.append({
            "id": "q_dup",
            "question": f"Found {analysis['duplicate_rows']} duplicate rows. What should we do?",
            "type": "radio",
            "column": None,
            "options": [
                {"id": "o1", "label": "Remove all duplicates", "value": "remove_duplicates"},
                {"id": "o2", "label": "Keep duplicates as-is", "value": "keep"},
            ]
        })
 
    has_missing_text = False
    has_missing_numeric = False
 
    for col in analysis["columns"]:
        if col["missing_count"] > 0:
            if col["type_category"] == "numeric":
                has_missing_numeric = True
            else:
                has_missing_text = True
 
    if has_missing_numeric:
        questions.append({
            "id": "q_miss_numeric",
            "question": "Some numeric columns have missing values. How should they be handled?",
            "type": "radio",
            "column": None,
            "options": [
                {"id": "o1", "label": "Fill with mean", "value": "fill_mean"},
                {"id": "o2", "label": "Fill with median", "value": "fill_median"},
                {"id": "o3", "label": "Fill with 0", "value": "fill_zero"},
                {"id": "o4", "label": "Remove rows with missing values", "value": "drop_rows"},
            ]
        })
 
    if has_missing_text:
        questions.append({
            "id": "q_miss_text",
            "question": "Some text columns have missing values. How should they be handled?",
            "type": "radio",
            "column": None,
            "options": [
                {"id": "o1", "label": "Fill with 'Unknown'", "value": "fill_unknown"},
                {"id": "o2", "label": "Fill with most frequent value", "value": "fill_mode"},
                {"id": "o3", "label": "Remove rows with missing values", "value": "drop_rows"},
                {"id": "o4", "label": "Keep as-is", "value": "keep"},
            ]
        })
 
    # Date columns
    date_cols = [c for c in analysis["columns"] if c["type_category"] == "date"]
    if date_cols:
        questions.append({
            "id": "q_date",
            "question": f"Date columns detected ({', '.join(c['name'] for c in date_cols)}). Standardize format?",
            "type": "radio",
            "column": None,
            "options": [
                {"id": "o1", "label": "Standardize to YYYY-MM-DD", "value": "yyyy-mm-dd"},
                {"id": "o2", "label": "Standardize to DD/MM/YYYY", "value": "dd/mm/yyyy"},
                {"id": "o3", "label": "Keep existing formats", "value": "keep"},
            ]
        })
 
    # Text casing
    text_cols = [c for c in analysis["columns"] if c["type_category"] == "text"]
    if text_cols:
        questions.append({
            "id": "q_case",
            "question": "Text columns may have inconsistent casing. How to standardize?",
            "type": "radio",
            "column": None,
            "options": [
                {"id": "o1", "label": "Title Case (e.g., Ahmed Khan)", "value": "title_case"},
                {"id": "o2", "label": "UPPER CASE", "value": "upper_case"},
                {"id": "o3", "label": "lower case", "value": "lower_case"},
                {"id": "o4", "label": "Keep existing casing", "value": "keep"},
            ]
        })
 
    return questions
 
 
def generate_summary(stats: Dict[str, Any]) -> str:
    try:
        prompt = f"""
You are a data analyst. Write a short, clear, friendly summary (3-5 sentences) of what was done to clean this data.
Stats: {json.dumps(stats)}
Be specific about numbers. Mention what was removed, fixed, or kept. End with a positive note.
Return only the summary text, no markdown.
"""
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Gemini summary generation failed: {e}")
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
