import os
import uuid
import pandas as pd
from fastapi import UploadFile, HTTPException
from config import UPLOAD_DIR, ALLOWED_EXTENSIONS, MAX_FILE_SIZE


def validate_file(file: UploadFile) -> str:
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    return ext


def generate_file_id() -> str:
    return str(uuid.uuid4())


def get_file_path(file_id: str, ext: str) -> str:
    upload_dir = os.path.abspath(UPLOAD_DIR)
    os.makedirs(upload_dir, exist_ok=True)
    return os.path.join(upload_dir, f"{file_id}{ext}")


async def save_upload(file: UploadFile, file_id: str, ext: str) -> str:
    path = get_file_path(file_id, ext)
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Max 10MB.")
    with open(path, "wb") as f:
        f.write(content)
    return path


def load_dataframe(file_id: str) -> tuple[pd.DataFrame, str]:
    for ext in [".xlsx", ".xls", ".csv"]:
        path = get_file_path(file_id, ext)
        if os.path.exists(path):
            if ext == ".csv":
                df = pd.read_csv(path, encoding="utf-8", encoding_errors="replace")
            else:
                df = pd.read_excel(path)
            return df, ext
    raise HTTPException(status_code=404, detail="File not found. Please re-upload.")


def save_output(df: pd.DataFrame, file_id: str, output_format: str) -> str:
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    out_id = f"{file_id}_output"
    if output_format == "csv":
        path = get_file_path(out_id, ".csv")
        df.to_csv(path, index=False)
    else:
        path = get_file_path(out_id, ".xlsx")
        df.to_excel(path, index=False)
    return path
