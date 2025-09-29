from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from ocr_module import ocr_pdf_first6
from ai_groq import extract_info
from compare_module import compare_records

app = FastAPI(title="OCR + AI PDF Extraction API")

# API 1: PDF -> OCR text
@app.post("/upload_pdf")
async def upload_pdf(file: UploadFile = File(...)):
    try:
        pdf_path = f"temp_{file.filename}"
        with open(pdf_path, "wb") as f:
            f.write(await file.read())

        text = ocr_pdf_first6(pdf_path)
        return JSONResponse(content={"ocr_text": text})

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


# API 2: OCR text -> JSON trích xuất
@app.post("/extract_text")
async def extract_text(ocr_text: str = Form(...)):
    try:
        data = extract_info(ocr_text)

        if "error" not in data:
            results = compare_records(data["phieu_chuyen"], data["hop_dong"])
            response = {
                "extracted_data": data,
                "comparison": results
            }
        else:
            response = {"error": data["error"]}

        return JSONResponse(content=response)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
