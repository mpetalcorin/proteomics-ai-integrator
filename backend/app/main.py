from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io

from app.analysis_utils import run_basic_analysis
from app.ml_utils import run_ml_prediction
from app.ai_report import generate_ai_summary
from app.analysis_utils import run_basic_analysis, run_differential_analysis
from fastapi.responses import FileResponse
from app.advanced_analysis import run_advanced_analysis
from app.report_utils import generate_pdf_report, generate_word_report

def read_uploaded_table(content: bytes, filename: str):
    if filename.endswith(".csv"):
        return pd.read_csv(io.BytesIO(content))
    if filename.endswith(".xlsx"):
        return pd.read_excel(io.BytesIO(content))
    if filename.endswith(".tsv") or filename.endswith(".txt"):
        return pd.read_csv(io.BytesIO(content), sep="\t")

    raise ValueError("Please upload a CSV, TSV, TXT, or XLSX file.")
app = FastAPI(
    title="Proteomics AI Integrator",
    description="AI and machine-learning platform for TMT/iTRAQ proteomics analysis",
    version="1.0.0",
)

import os

frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://proteomics-ai-integrator.vercel.app",
        "https://proteomics-ai-integrator-t7cusongq-mpetalcorins-projects.vercel.app",
        frontend_origin,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "Proteomics AI Integrator backend is running",
        "modules": [
            "TMT/iTRAQ abundance analysis",
            "PCA",
            "differential protein analysis",
            "machine-learning prediction",
            "AI biological report generation",
        ],
    }


@app.post("/api/analyze")
async def analyze_file(file: UploadFile = File(...)):
    content = await file.read()

    if file.filename.endswith(".csv"):
        df = pd.read_csv(io.BytesIO(content))
    elif file.filename.endswith(".xlsx"):
        df = pd.read_excel(io.BytesIO(content))
    elif file.filename.endswith(".tsv") or file.filename.endswith(".txt"):
        df = pd.read_csv(io.BytesIO(content), sep="\t")
    else:
        return {"error": "Please upload a CSV, TSV, TXT, or XLSX file."}

    result = run_basic_analysis(df)

    return result


@app.post("/api/differential")
async def differential_analysis(file: UploadFile = File(...)):
    content = await file.read()

    if file.filename.endswith(".csv"):
        df = pd.read_csv(io.BytesIO(content))
    elif file.filename.endswith(".xlsx"):
        df = pd.read_excel(io.BytesIO(content))
    elif file.filename.endswith(".tsv") or file.filename.endswith(".txt"):
        df = pd.read_csv(io.BytesIO(content), sep="\t")
    else:
        return {"error": "Please upload a CSV, TSV, TXT, or XLSX file."}

    result = run_differential_analysis(df)

    return result


@app.post("/api/predict")
async def predict_file(file: UploadFile = File(...)):
    content = await file.read()

    if file.filename.endswith(".csv"):
        df = pd.read_csv(io.BytesIO(content))
    elif file.filename.endswith(".xlsx"):
        df = pd.read_excel(io.BytesIO(content))
    elif file.filename.endswith(".tsv") or file.filename.endswith(".txt"):
        df = pd.read_csv(io.BytesIO(content), sep="\t")
    else:
        return {"error": "Please upload a CSV, TSV, TXT, or XLSX file."}

    result = run_ml_prediction(df)

    return result


@app.post("/api/ai-report")
async def ai_report(file: UploadFile = File(...)):
    content = await file.read()

    if file.filename.endswith(".csv"):
        df = pd.read_csv(io.BytesIO(content))
    elif file.filename.endswith(".xlsx"):
        df = pd.read_excel(io.BytesIO(content))
    elif file.filename.endswith(".tsv") or file.filename.endswith(".txt"):
        df = pd.read_csv(io.BytesIO(content), sep="\t")
    else:
        return {"error": "Please upload a CSV, TSV, TXT, or XLSX file."}

    analysis = run_basic_analysis(df)
    ml_result = run_ml_prediction(df)
    report = generate_ai_summary(analysis, ml_result)

    return {"report": report}

@app.post("/api/advanced")
async def advanced_file(file: UploadFile = File(...)):
    content = await file.read()

    try:
        df = read_uploaded_table(content, file.filename)
        result = run_advanced_analysis(df)
        return result
    except Exception as error:
        return {"error": str(error)}


@app.post("/api/report/pdf")
async def pdf_report(file: UploadFile = File(...)):
    content = await file.read()

    try:
        df = read_uploaded_table(content, file.filename)
        result = run_advanced_analysis(df)

        if "warning" in result or "error" in result:
            return result

        pdf_path = generate_pdf_report(result)

        return FileResponse(
            pdf_path,
            filename="proteomics_ai_integrator_report.pdf",
            media_type="application/pdf",
        )

    except Exception as error:
        return {"error": str(error)}


@app.post("/api/report/word")
async def word_report(file: UploadFile = File(...)):
    content = await file.read()

    try:
        df = read_uploaded_table(content, file.filename)
        result = run_advanced_analysis(df)

        if "warning" in result or "error" in result:
            return result

        word_path = generate_word_report(result)

        return FileResponse(
            word_path,
            filename="proteomics_ai_integrator_report.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

    except Exception as error:
        return {"error": str(error)}