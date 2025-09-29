from pdf2image import convert_from_path
import pytesseract
from concurrent.futures import ThreadPoolExecutor

def ocr_page(image, lang="vie"):
    """OCR 1 trang ảnh"""
    return pytesseract.image_to_string(image, lang=lang)

def ocr_pdf_first6(pdf_path: str, lang: str = "vie") -> str:
    """
    OCR song song chỉ 3 trang đầu của PDF
    """
    print(f"===== OCR file {pdf_path} (song song, 3 trang đầu) =====")
    # Chỉ load 3 trang đầu
    images = convert_from_path(pdf_path, first_page=1, last_page=3)

    texts = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        # Map mỗi trang với hàm OCR
        future_to_page = {executor.submit(ocr_page, img, lang): idx+1 for idx, img in enumerate(images)}
        for future in future_to_page:
            page_num = future_to_page[future]
            try:
                page_text = future.result()
                texts.append(page_text)
                print(f"--> OCR xong trang {page_num}")
            except Exception as e:
                print(f"❌ Lỗi OCR trang {page_num}: {e}")
                texts.append("")

    return "\n".join(texts)
