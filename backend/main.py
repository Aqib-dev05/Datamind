from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from models.schemas import QuestionsResponse, UserAnswers, ProcessResponse
from utils.file_handler import validate_file, generate_file_id, save_upload, load_dataframe, save_output
from utils.data_analyzer import analyze_dataframe, get_preview
from services.gemini_service import generate_questions, generate_summary
from services.excel_service import process_dataframe
from config import UPLOAD_DIR
import os

app = FastAPI(title="Excel AI Analyzer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Excel AI Analyzer API is running"}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    ext = validate_file(file)
    file_id = generate_file_id()
    await save_upload(file, file_id, ext)
    df, _ = load_dataframe(file_id)

    analysis = analyze_dataframe(df)
    preview = get_preview(df, rows=5)

    column_info = [
        {
            "name": col["name"],
            "dtype": col["dtype"],
            "missing_count": col["missing_count"],
            "missing_pct": col["missing_pct"],
            "type_category": col["type_category"],
            "sample_values": col["sample_values"],
        }
        for col in analysis["columns"]
    ]

    return {
        "file_id": file_id,
        "filename": file.filename,
        "rows": analysis["total_rows"],
        "columns": analysis["total_columns"],
        "duplicate_rows": analysis["duplicate_rows"],
        "total_missing": analysis["total_missing"],
        "preview": preview,
        "column_info": column_info,
    }


@app.get("/questions/{file_id}")
async def get_questions(file_id: str):
    df, _ = load_dataframe(file_id)
    analysis = analyze_dataframe(df)
    questions = generate_questions(analysis)
    return {"file_id": file_id, "questions": questions}


@app.post("/process")
async def process_file(body: UserAnswers):
    df, _ = load_dataframe(body.file_id)
    cleaned_df, stats = process_dataframe(df, body.answers)
    output_path = save_output(cleaned_df, body.file_id, body.output_format)
    summary = generate_summary(stats)

    filename = os.path.basename(output_path)
    return {
        "success": True,
        "message": "File processed successfully",
        "download_url": f"/download/{body.file_id}/{body.output_format}",
        "summary": summary,
        "stats": stats,
    }


@app.get("/download/{file_id}/{fmt}")
async def download_file(file_id: str, fmt: str):
    if fmt not in {"csv", "xlsx"}:
        raise HTTPException(status_code=400, detail="Invalid format")
    ext = ".csv" if fmt == "csv" else ".xlsx"
    path = os.path.join(UPLOAD_DIR, f"{file_id}_output{ext}")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    media_type = "text/csv" if fmt == "csv" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return FileResponse(path, media_type=media_type, filename=f"cleaned_data{ext}")
