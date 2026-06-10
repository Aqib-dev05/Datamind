import os
from dotenv import load_dotenv
 
load_dotenv()
 
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
UPLOAD_DIR = "uploads"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {".xlsx", ".xls", ".csv"}
