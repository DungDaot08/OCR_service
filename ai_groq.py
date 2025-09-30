# ai_module.py
import os
import re
import json
from groq import Groq  # thay vì openai

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

def extract_info1(full_text: str):
    """
    Gửi văn bản OCR qua Groq để trích xuất thông tin
    """
    prompt = f"""
Bạn là hệ thống phân tích văn bản phiếu chuyển nhượng đất đai.

⚠️ Quy tắc trích xuất:
1. Luôn tìm **họ tên** sau từ khóa "Ông", "Bà" hoặc "Họ tên". Không ghi cả từ "Ông", "Bà" vào trường họ tên.
2. Luôn tìm **CCCD** sau từ khóa "CCCD số", "CMND số".
3. Trong **Phiếu chuyển**: chỉ có thông tin **người mua**.
4. Nếu không thấy thông tin "tài sản gắn liền với đất" → trả về "Không".
5. Không bỏ trống các trường nếu có dữ liệu trong văn bản OCR, nếu không thấy thì để "".
6. Tên các trường JSON phải **chính xác y hệt** như mẫu.
7. Chỉ trả về JSON hợp lệ, không thêm giải thích.

Cấu trúc JSON mong muốn:
{{
  "phieu_chuyen": {{ 
    "nguoi_mua": [{{"ho_ten": "Tên đầy đủ", "cccd": "Số CCCD"}}],
    "dia_chi_mua": "",
    "so_thua": "",
    "to_ban_do": "",
    "dien_tich": "",
    "loai_dat": "", (Chính là mục đích sử dụng đất)
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
            response_format={"type": "json_object"}
        )
        raw_output = response.choices[0].message.content
        print("===== RAW GPT OUTPUT =====")
        print(raw_output)
        return safe_json_parse(raw_output)

    except Exception as e:
        print("❌ Lỗi khi gọi Groq:", e)
        return {"error": str(e)}


def extract_info(full_text: str):
    """
    Gửi văn bản OCR qua Groq để trích xuất thông tin
    """
    prompt = f"""
Bạn là hệ thống phân tích văn bản hợp đồng và phiếu chuyển nhượng đất đai để só sánh thông tin.

⚠️ Quy tắc trích xuất:
1. Luôn tìm **họ tên** sau từ khóa "Ông", "Bà" hoặc "Họ tên". Không ghi cả từ "Ông", "Bà" vào trường họ tên.
2. Luôn tìm **CCCD** sau từ khóa "CCCD số", "CMND số".
3. Trong **Phiếu chuyển**: chỉ có thông tin **người mua**, **địa chỉ người mua**.
4. Trong **Hợp đồng**: có cả **người bán** và **người mua**, có thể nhiều người.
5. Những thông tin của **Phiếu chuyển** tìm ở trang 1 và 2, những thông tin của **Hợp đồng** tìm từ trang 3 trở đi.
6. Nếu không thấy thông tin "tài sản gắn liền với đất" → trả về "Không".
7. Không bỏ trống các trường nếu có dữ liệu trong văn bản OCR, nếu không thấy thì để "".
8. Tên các trường JSON phải **chính xác y hệt** như mẫu.
9. Lưu ý các thông tin của **Phiếu chuyển** và **Hợp đồng** phải tìm đúng vị trí, không phải lúc nào các thông tin 2 văn bản cũng giống nhau. 
10. Đừng bao giờ copy nội dung những mục trong **Phiếu chuyển** và **Hợp đồng vào nhau**.
11. Chỉ trả về JSON hợp lệ, không thêm giải thích.

Cấu trúc JSON mong muốn:
{{
  "phieuchuyen": {{ 
    "nguoi_mua": [{{"ho_ten": "Tên đầy đủ", "cccd": "Số CCCD"}}],
    "dia_chi_mua": "",
    "so_thua": "",
    "to_ban_do": "",
    "dien_tich": "",
    "loai_dat": "", (Chính là mục đích sử dụng đất)
    "tai_san_gan_voi_dat": ""
  }},
  "hopdong": {{ 
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
            response_format={"type": "json_object"}
        )
        raw_output = response.choices[0].message.content
        print("===== RAW GPT OUTPUT =====")
        print(raw_output)
        return safe_json_parse(raw_output)

    except Exception as e:
        print("❌ Lỗi khi gọi Groq:", e)
        return {"error": str(e)}
