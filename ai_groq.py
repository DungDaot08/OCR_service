# ai_module.py
import os
import re
import json
from groq import Groq  # thay vì openai

# Lấy API key từ biến môi trường (khuyến nghị) hoặc hardcode để test
client = Groq(api_key=os.getenv("GROQ_API_KEY", "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"))

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
    Gửi văn bản OCR qua Groq để trích xuất thông tin
    """
    prompt = f"""
Bạn là hệ thống phân tích văn bản hợp đồng và phiếu chuyển nhượng đất đai.

⚠️ Quy tắc trích xuất:
1. Luôn tìm **họ tên** sau từ khóa "Ông", "Bà" hoặc "Họ tên".
2. Luôn tìm **CCCD** sau từ khóa "CCCD số", "CMND số".
   - Nếu không chắc, lấy nguyên văn số sau "CCCD số".
3. Trong **Phiếu chuyển**: chỉ có thông tin **người mua**. Trả về danh sách người mua.
4. Trong **Hợp đồng**: có cả **người bán** và **người mua**. Trích xuất đầy đủ. Trong hợp đồng **người bán** và **người mua** có thể có nhiều người, hãy lấy đầy đủ thông tin từng người.
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
    "loai_dat": "",(Chính là mục đích sử dụng đất)
    "tai_san_gan_voi_dat": ""
  }},
  "hop_dong": {{
    "nguoi_ban": [{{"ho_ten": "Tên đầy đủ", "cccd": "Số CCCD"}}],
    "dia_chi_ban": "",
    "nguoi_mua": [{{"ho_ten": "Tên đầy đủ", "cccd": "Số CCCD"}}],
    "dia_chi_mua": "",
    "so_thua": "",
    "to_ban_do": "",
    "dien_tich": "",
    "loai_dat": "",(Chính là mục đích sử dụng đất)
    "tai_san_gan_voi_dat": ""
  }}
}}

Văn bản OCR:

{full_text}
"""
    MODEL_NAME = "openai/gpt-oss-20b"

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,  
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}  # ép trả JSON
        )

        raw_output = response.choices[0].message.content
        print("===== RAW GPT OUTPUT =====")
        print(raw_output)

        return safe_json_parse(raw_output)

    except Exception as e:
        print("❌ Lỗi khi gọi Groq:", e)
        return {"error": str(e)}
