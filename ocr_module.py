from pdf2image import convert_from_path
import pytesseract

def ocr_pdf(pdf_path: str, lang: str = "vie") -> str:
    """Đọc PDF và trả về toàn bộ text bằng OCR"""
    print(f"===== OCR file {pdf_path} =====")
    images = convert_from_path(pdf_path)
    text = ""
    for img in images:
        text += pytesseract.image_to_string(img, lang=lang) + "\n"
    return text

def ocr_page(image, lang="vie"):
    """OCR 1 trang ảnh"""
    return pytesseract.image_to_string(image, lang=lang)

def ocr_pdf_filtered(pdf_path: str, lang: str = "vie") -> str:
    """
    OCR PDF nhưng chỉ lấy:
    - 3 trang đầu tiên kể từ trang chứa 'Phiếu chuyển'
    - 3 trang đầu tiên kể từ trang chứa 'Hợp đồng'
    """
    print(f"===== OCR file {pdf_path} (lọc trang) =====")
    images = convert_from_path(pdf_path)

    selected_texts = []
    found_phieu = 0
    found_hd = 0
    capture_phieu = False
    capture_hd = False

    for idx, img in enumerate(images):
        text = ocr_page(img, lang=lang)

        # Nếu chưa bật capture và tìm thấy từ khóa
        if not capture_phieu and "phiếu chuyển" in text.lower():
            capture_phieu = True
            found_phieu = 0
            print(f"--> Bắt đầu lấy từ trang {idx+1} (Phiếu chuyển)")

        if not capture_hd and "hợp đồng" in text.lower():
            capture_hd = True
            found_hd = 0
            print(f"--> Bắt đầu lấy từ trang {idx+1} (Hợp đồng)")

        # Nếu đang capture thì lấy thêm tối đa 3 trang
        if capture_phieu and found_phieu < 3:
            selected_texts.append(text)
            found_phieu += 1
            if found_phieu == 3:
                capture_phieu = False

        if capture_hd and found_hd < 3:
            selected_texts.append(text)
            found_hd += 1
            if found_hd == 3:
                capture_hd = False

        # Nếu đã lấy đủ cả 2 loại thì dừng
        if found_phieu == 3 and found_hd == 3:
            break

    return "\n".join(selected_texts)

def ocr_pdf_first6(pdf_path: str, lang: str = "vie") -> str:
    """
    OCR chỉ 10 trang đầu tiên của PDF
    """
    print(f"===== OCR file {pdf_path} (chỉ 10 trang đầu) =====")
    images = convert_from_path(pdf_path, first_page=1, last_page=1)

    texts = []
    for idx, img in enumerate(images):
        page_text = pytesseract.image_to_string(img, lang=lang)
        texts.append(page_text)
        print(f"--> Đã OCR trang {idx+1}")

    return "\n".join(texts)