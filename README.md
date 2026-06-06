# DataMind AI — Excel/CSV Cleaner

AI-powered data cleaning tool. Upload messy Excel or CSV files, answer AI-generated questions, and download a cleaned file.

## Features
- Upload `.xlsx`, `.xls`, or `.csv` files
- AI (Gemini) analyzes the file and asks smart questions
- Checkbox/radio options for cleaning preferences
- Download cleaned file as Excel or CSV
- AI-generated summary of what was changed

## Setup

### 1. Backend (FastAPI + Python)

```bash
cd backend
pip install -r requirements.txt
```

Create `.env` file (already included):
```
GEMINI_API_KEY=your_gemini_api_key_here
```
Get your Gemini API key from: https://aistudio.google.com/app/apikey

Run backend:
```bash
uvicorn main:app --reload --port 8000
```

### 2. Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: http://localhost:5173
Backend runs at: http://localhost:8000

## Project Structure
```
excel-ai-analyzer/
├── backend/
│   ├── main.py              # FastAPI routes
│   ├── config.py            # Environment config
│   ├── requirements.txt
│   ├── services/
│   │   ├── gemini_service.py    # Gemini AI integration
│   │   └── excel_service.py     # Data cleaning logic
│   ├── models/
│   │   └── schemas.py           # Pydantic models
│   └── utils/
│       ├── file_handler.py      # File upload/save
│       └── data_analyzer.py     # Data analysis
└── frontend/
    └── src/
        ├── pages/
        │   ├── Home.jsx         # Upload page
        │   ├── Analysis.jsx     # Questions page
        │   └── Results.jsx      # Results + download
        ├── context/
        │   └── AppContext.jsx   # Global state
        └── services/
            └── api.js           # API calls
```
