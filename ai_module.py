# ai_module.py
import os
import re
import json
from openai import OpenAI

# Lấy API key từ biến môi trường
client = OpenAI(api_key="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")

def safe_json_parse(text: str):
    """Parse JSON an toàn, lọc ra block JSON hợp lệ"""
    try:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except Exception as e:
        print("❌ Lỗi parse JSON:", e)
    return {"error": "Không parse được JSON"}

def extract_info(full_text: str):
    """
    Gửi văn bản OCR qua GPT để trích xuất thông tin
    """
    prompt = f"""
Bạn là hệ thống phân tích văn bản hợp đồng và phiếu chuyển nhượng đất đai.

⚠️ Quy tắc trích xuất:
1. Luôn tìm **họ tên** sau từ khóa "Ông", "Bà" hoặc "Họ tên".
2. Luôn tìm **CCCD** sau từ khóa "CCCD số", "CMND số".
   - Nếu không chắc, lấy nguyên văn số sau "CCCD số".
3. Trong **Phiếu chuyển**: chỉ có thông tin **người mua**. Trả về danh sách người mua.
4. Trong **Hợp đồng**: có cả **người bán** và **người mua**. Trích xuất đầy đủ.
5. Nếu không thấy thông tin "tài sản gắn liền với đất" → trả về "Không".
6. Không bỏ trống các trường nếu có dữ liệu trong văn bản OCR. Nếu không tìm thấy thì để "" (chuỗi rỗng).
7. Chỉ trả về JSON hợp lệ, không thêm giải thích.

Cấu trúc JSON mong muốn:
{{
  "phieu_chuyen": {{
    "nguoi_mua": [{{"ho_ten": "Tên đầy đủ", "cccd": "Số CCCD"}}],
    "dia_chi_mua": "",
    "so_thua": "",
    "to_ban_do": "",
    "dien_tich": "",
    "loai_dat": "",
    "tai_san": ""
  }},
  "hop_dong": {{
    "nguoi_ban": [{{"ho_ten": "Tên đầy đủ", "cccd": "Số CCCD"}}],
    "dia_chi_ban": "",
    "nguoi_mua": [{{"ho_ten": "Tên đầy đủ", "cccd": "Số CCCD"}}],
    "dia_chi_mua": "",
    "so_thua": "",
    "to_ban_do": "",
    "dien_tich": "",
    "loai_dat": "",
    "tai_san": ""
  }}
}}

Văn bản OCR:

{full_text}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}  # ép trả JSON
        )

        raw_output = response.choices[0].message.content
        print("===== RAW GPT OUTPUT =====")
        print(raw_output)  # log để debug

        return safe_json_parse(raw_output)

    except Exception as e:
        print("❌ Lỗi khi gọi GPT:", e)
        return {"error": str(e)}
