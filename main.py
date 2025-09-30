# main_api.py
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from ocr_module import ocr_pdf_with_boxes, crop_fields_from_ocr
from ai_groq import extract_info
import os
import uuid

app = FastAPI(title="OCR + AI PDF Extraction API with Field Images")

# Thư mục lưu ảnh tạm
TEMP_IMAGE_DIR = "temp_crops"
os.makedirs(TEMP_IMAGE_DIR, exist_ok=True)

from difflib import SequenceMatcher

def compare_phieu_hop(phieu_chuyen: dict, hop_dong: dict) -> dict:
    """
    So sánh thông tin giữa phiếu chuyển và hợp đồng:
    - So sánh họ tên, CCCD, địa chỉ người mua ở phiếu chuyển
      với người mua đầu tiên ở hợp đồng.
    - So sánh các trường chung: so_thua, to_ban_do, dien_tich, loai_dat, tai_san_gan_voi_dat
    """
    result = {}
    try:
        hop_dong_nguoi_mua = hop_dong.get("nguoi_mua", [])
        if not hop_dong_nguoi_mua:
            return {"error": "Hợp đồng không có người mua"}

        first_hd_mua = hop_dong_nguoi_mua[0]

        phieu_nguoi_mua = phieu_chuyen.get("nguoi_mua", [{}])[0]

        # So sánh thông tin người mua
        mua_fields = ["ho_ten", "cccd"]
        for f in mua_fields:
            pc_val = phieu_nguoi_mua.get(f, "").strip()
            hd_val = first_hd_mua.get(f, "").strip()
            ratio = SequenceMatcher(None, pc_val, hd_val).ratio() if pc_val and hd_val else 0.0
            result[f] = {"phieuchuyen": pc_val, "hopdong": hd_val, "similarity": round(ratio, 2)}

        # So sánh các trường chung
        common_fields = ["so_thua", "to_ban_do", "dien_tich", "loai_dat", "tai_san_gan_voi_dat", "dia_chi_mua"]
        for f in common_fields:
            pc_val = phieu_chuyen.get(f, "").strip()
            hd_val = hop_dong.get(f, "").strip()
            ratio = SequenceMatcher(None, pc_val, hd_val).ratio() if pc_val and hd_val else 0.0
            result[f] = {"phieuchuyen": pc_val, "hopdong": hd_val, "similarity": round(ratio, 2)}

    except Exception as e:
        result["error"] = str(e)

    return result

@app.post("/extract_pdf")
async def extract_pdf(file: UploadFile = File(...)):
    try:
        pdf_path = f"temp_{uuid.uuid4().hex}_{file.filename}"
        with open(pdf_path, "wb") as f:
            f.write(await file.read())

        # 1. OCR với bounding box
        ocr_result = ocr_pdf_with_boxes(pdf_path)

        # 2. Tách text theo từng trang
        ocr_pages_text = [
            {"page": p["page"], "text": p["text"]}
            for p in ocr_result["ocr_pages"]
        ]

        # 3. Gửi toàn bộ text (ghép tất cả trang) cho AI Groq
        full_ocr_text = ""
        for page in ocr_pages_text:
            full_ocr_text += f"--- Trang {page['page']} ---\n{page['text']}\n\n"

        # Gọi AI
        extracted_data = extract_info(full_ocr_text)

        image_files = []
        if "error" not in extracted_data:
            # 4. Crop ảnh từng field từ bounding box
            image_files = crop_fields_from_ocr(ocr_result, extracted_data, TEMP_IMAGE_DIR)

        response = {
            "ocr_text": ocr_pages_text,  # list text theo trang
            "extracted_data": extracted_data,
            "image_files": image_files
        }
        
        if "error" not in extracted_data:
            phieu_chuyen = extracted_data.get("phieuchuyen", {})
            hop_dong = extracted_data.get("hopdong", {})
            comparison = compare_phieu_hop(phieu_chuyen, hop_dong)
            response["comparison"] = comparison

        return JSONResponse(content=response)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/extract_pdf1")
async def extract_pdf1(file: UploadFile = File(...)):
    try:
        pdf_path = f"temp_{uuid.uuid4().hex}_{file.filename}"
        with open(pdf_path, "wb") as f:
            f.write(await file.read())

        # 1. OCR với bounding box
        ocr_result = ocr_pdf_with_boxes(pdf_path)

        # 2. Tách text theo từng trang
        ocr_pages_text = [
            {"page": p["page"], "text": p["text"]}
            for p in ocr_result["ocr_pages"]
        ]

        # 3. Gửi toàn bộ text (ghép tất cả trang) cho AI Groq
        full_ocr_text = ""
        for page in ocr_pages_text:
            full_ocr_text += f"--- Trang {page['page']} ---\n{page['text']}\n\n"

        # Gọi AI
        #extracted_data = extract_info(full_ocr_text)

        #image_files = []
        #if "error" not in extracted_data:
        #    # 4. Crop ảnh từng field từ bounding box
        #    image_files = crop_fields_from_ocr(ocr_result, extracted_data, TEMP_IMAGE_DIR)

        response = {
            "ocr_text": full_ocr_text,  # list text theo trang
            "extracted_data": ocr_result,
            #"image_files": image_files
        }
        
        #if "error" not in extracted_data:
        #    phieu_chuyen = extracted_data.get("phieu_chuyen", {})
        #    hop_dong = extracted_data.get("hop_dong", {})
        #    comparison = compare_phieu_hop(phieu_chuyen, hop_dong)
        #    response["comparison"] = comparison

        return JSONResponse(content=response)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)