# main_api.py
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from ocr_module import ocr_pdf_first6
from ai_groq import extract_info
from compare_module import compare_records
#import export_excel if you want to support Excel export

app = FastAPI(title="OCR + AI PDF Extraction API")

@app.post("/extract")
async def extract_pdf(file: UploadFile = File(...)):
    try:
        # 1. Lưu tạm file upload
        pdf_path = f"temp_{file.filename}"
        with open(pdf_path, "wb") as f:
            f.write(await file.read())

        # 2. OCR
        text = ocr_pdf_first6(pdf_path)

        # 3. AI lọc Phiếu chuyển + Hợp đồng
        data = extract_info(text)

        # 4. So khớp dữ liệu
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
