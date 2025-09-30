import os
from pdf2image import convert_from_path
import pytesseract
from pytesseract import Output
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
from difflib import SequenceMatcher
import uuid
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Giả sử bạn để tesseract trong thư mục dự án: ./tesseract/tesseract.exe
TESSERACT_PATH = os.path.join(BASE_DIR, "tesseract", "tesseract.exe")
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

POPPLER_PATH = os.path.join(BASE_DIR, "poppler", "Library", "bin")  # thư mục chứa poppler.exe

# -------------------------
# OCR 1 trang với bounding box
# -------------------------
def ocr_page_with_bbox(image, lang="vie"):
    """OCR 1 trang, trả về text và bbox từng từ"""
    data = pytesseract.image_to_data(image, lang=lang, output_type=Output.DICT)
    words = []
    n_boxes = len(data['text'])
    for i in range(n_boxes):
        text = data['text'][i].strip()
        if text:
            x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
            words.append({"text": text, "bbox": [x, y, x + w, y + h]})
    return words

# -------------------------
# OCR toàn bộ PDF (3 trang đầu)
# -------------------------
def ocr_pdf_with_boxes(pdf_path: str, lang: str = "vie") -> dict:
    """OCR 3 trang đầu, trả về text + bbox"""
    print(f"===== OCR file {pdf_path} (3 trang đầu, có bbox) =====")
    images = convert_from_path(pdf_path, first_page=1, last_page=6, dpi=100, poppler_path=POPPLER_PATH)
    results = {"pdf_file": pdf_path, "ocr_pages": []}

    def process_page(idx, img):
        words = ocr_page_with_bbox(img, lang)
        page_text = " ".join([w["text"] for w in words])
        results["ocr_pages"].append({"page": idx + 1, "text": page_text, "words": words})
        print(f"--> OCR xong trang {idx+1}")
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(process_page, idx, img) for idx, img in enumerate(images)]
        for future in futures:
            future.result()

    results["ocr_pages"].sort(key=lambda x: x["page"])
    results["text"] = " ".join([p["text"] for p in results["ocr_pages"]])
    #results["images"] = images  # giữ ảnh gốc của từng trang để crop
    return results

# -------------------------
# Fuzzy match bbox cho từng field
# -------------------------
def find_bbox_for_field(field_text, words):
    """Fuzzy match text field với từ OCR, trả về bbox"""
    words_text = [w["text"] for w in words]
    n = len(words_text)
    field_len = len(field_text.split())

    best_ratio = 0
    best_bbox = None

    for i in range(n - field_len + 1):
        candidate = " ".join(words_text[i:i+field_len])
        ratio = SequenceMatcher(None, candidate, field_text).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            xs = [words[j]["bbox"][0] for j in range(i, i+field_len)]
            ys = [words[j]["bbox"][1] for j in range(i, i+field_len)]
            xe = [words[j]["bbox"][2] for j in range(i, i+field_len)]
            ye = [words[j]["bbox"][3] for j in range(i, i+field_len)]
            best_bbox = [min(xs), min(ys), max(xe), max(ye)]
    return best_bbox if best_ratio > 0.8 else None


def crop_fields_from_ocr1(ocr_result: dict, ai_json: dict, output_dir: str):
    import os
    os.makedirs(output_dir, exist_ok=True)
    image_files = []

    n_pages = len(ocr_result["ocr_pages"])

    def get_page_indices(top_level_key):
        if top_level_key == "phieuchuyen":
            return range(n_pages)  # đầu → cuối
        elif top_level_key == "hopdong":
            return reversed(range(n_pages))
            #return range(n_pages)# cuối → đầu
        return range(n_pages)

    def safe_filename(s: str):
        import re
        s = re.sub(r"[^0-9a-zA-Z_]+", "_", s)
        return s.strip("_") + ".png"

    def process_dict(d, parent_key=""):
        for key, value in d.items():
            if isinstance(value, dict):
                process_dict(value, f"{parent_key}{key}_")
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        top_level_key = parent_key.split("_")[0]
                        if top_level_key == "hopdong" and key == "nguoi_mua" and i > 0:
                            continue
                        process_dict(item, f"{parent_key}{key}_{i}_")
            elif isinstance(value, str) and value.strip():
                top_level_key = parent_key.split("_")[0]
                pages_to_check = list(get_page_indices(top_level_key))

                last_filename = None
                for page_idx in pages_to_check:
                    words = ocr_result["ocr_pages"][page_idx]["words"]
                    img = ocr_result["images"][page_idx]
                    bbox = find_bbox_for_field(value, words)
                    if bbox:
                        crop_img = img.crop(bbox)
                        filename = safe_filename(f"{parent_key}{key}")
                        full_path = os.path.join(output_dir, filename)
                        crop_img.save(full_path)
                        if top_level_key == "phieuchuyen":
                            image_files.append(full_path)
                            break
                        elif top_level_key == "hopdong":
                            last_filename = full_path
                if top_level_key == "hopdong" and last_filename:
                    image_files.append(last_filename)

    process_dict(ai_json)
    if "images" in ocr_result:
        del ocr_result["images"]

    return image_files

def crop_fields_from_ocr2(ocr_result: dict, ai_json: dict, output_dir: str):
    import os, uuid, re
    os.makedirs(output_dir, exist_ok=True)
    image_files = []

    n_pages = len(ocr_result["ocr_pages"])

    def get_page_indices(top_level_key):
        if top_level_key == "phieuchuyen":
            return range(n_pages)  # đầu → cuối
        elif top_level_key == "hopdong":
            return reversed(range(n_pages))
        return range(n_pages)

    def safe_filename(s: str):
        # Loại bỏ ký tự đặc biệt
        s = re.sub(r"[^0-9a-zA-Z_]+", "_", s)
        return s.strip("_")

    def process_dict(d, parent_key=""):
        for key, value in d.items():
            if isinstance(value, dict):
                process_dict(value, f"{parent_key}{key}_")
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        top_level_key = parent_key.split("_")[0]
                        if top_level_key == "hopdong" and key == "nguoi_mua" and i > 0:
                            continue
                        process_dict(item, f"{parent_key}{key}_{i}_")
            elif isinstance(value, str) and value.strip():
                top_level_key = parent_key.split("_")[0]
                pages_to_check = list(get_page_indices(top_level_key))

                last_filename = None
                for page_idx in pages_to_check:
                    words = ocr_result["ocr_pages"][page_idx]["words"]
                    img = ocr_result["images"][page_idx]
                    bbox = find_bbox_for_field(value, words)
                    if bbox:
                        crop_img = img.crop(bbox)
                        # Tạo tên file: parent_key + key + uuid
                        filename = f"{safe_filename(parent_key + key)}.png"
                        full_path = os.path.join(output_dir, filename)
                        crop_img.save(full_path)
                        if top_level_key == "phieuchuyen":
                            image_files.append(full_path)
                            break
                        elif top_level_key == "hopdong":
                            last_filename = full_path
                if top_level_key == "hopdong" and last_filename:
                    image_files.append(last_filename)

    process_dict(ai_json)

    if "images" in ocr_result:
        del ocr_result["images"]

    return image_files


def crop_fields_from_ocr(ocr_result: dict, ai_json: dict, output_dir: str):
    import os, uuid, re
    os.makedirs(output_dir, exist_ok=True)
    image_files = []

    n_pages = len(ocr_result["ocr_pages"])

    # Giới hạn trang cho từng loại văn bản
    def get_page_indices(top_level_key):
        if top_level_key == "phieuchuyen":
        # Lấy trang 1,2
            return [i for i in range(len(ocr_result["ocr_pages"])) if ocr_result["ocr_pages"][i]["page"] in (1,2)]
        elif top_level_key == "hopdong":
        # Lấy trang 3,4,5
            return [i for i in range(len(ocr_result["ocr_pages"])) if ocr_result["ocr_pages"][i]["page"] in (3,4,5)]
        return list(range(len(ocr_result["ocr_pages"])))


    def safe_filename(s: str):
        s = re.sub(r"[^0-9a-zA-Z_]+", "_", s)
        return s.strip("_")

    def process_dict(d, parent_key=""):
        for key, value in d.items():
            if isinstance(value, dict):
                process_dict(value, f"{parent_key}{key}_")
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        top_level_key = parent_key.split("_")[0]
                        if top_level_key == "hopdong" and key == "nguoi_mua" and i > 0:
                            continue
                        process_dict(item, f"{parent_key}{key}_{i}_")
            elif isinstance(value, str) and value.strip():
                top_level_key = parent_key.split("_")[0]
                pages_to_check = get_page_indices(top_level_key)

                last_filename = None
                for page_idx in pages_to_check:
                    words = ocr_result["ocr_pages"][page_idx]["words"]
                    img = ocr_result["images"][page_idx]
                    bbox = find_bbox_for_field(value, words)
                    if bbox:
                        crop_img = img.crop(bbox)
                        filename = f"{safe_filename(parent_key + key)}.png"
                        full_path = os.path.join(output_dir, filename)
                        crop_img.save(full_path)
                        if top_level_key == "phieuchuyen":
                            image_files.append(full_path)
                            break
                        elif top_level_key == "hopdong":
                            last_filename = full_path
                if top_level_key == "hopdong" and last_filename:
                    image_files.append(last_filename)

    process_dict(ai_json)

    if "images" in ocr_result:
        del ocr_result["images"]

    return image_files



