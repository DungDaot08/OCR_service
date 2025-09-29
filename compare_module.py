from difflib import SequenceMatcher

def similarity(a: str, b: str) -> float:
    """Tính % giống nhau giữa 2 chuỗi"""
    return SequenceMatcher(None, str(a), str(b)).ratio() * 100

def compare_records(phieu: dict, hopdong: dict):
    """
    So khớp dữ liệu giữa Phiếu chuyển và Hợp đồng
    Trả về list dict để dễ export Excel
    """
    fields = {
        "ho_ten": "Họ và tên",
        "cccd": "Số CCCD",
        "dia_chi_mua": "Địa chỉ người mua",
        "dia_chi_ban": "Địa chỉ người bán",
        "so_thua": "Số thửa",
        "to_ban_do": "Tờ bản đồ",
        "dien_tich": "Diện tích",
        "loai_dat": "Loại đất",
        "tai_san": "Tài sản gắn liền"
    }

    results = []
    for key, label in fields.items():
        val1 = phieu.get(key, "")
        val2 = hopdong.get(key, "")
        score = similarity(val1, val2)

        # Màu theo ngưỡng
        if score == 100:
            level = "XANH"
        elif score >= 85:
            level = "VÀNG"
        else:
            level = "ĐỎ"

        results.append({
            "truong": label,
            "phieu_chuyen": val1,
            "hop_dong": val2,
            "ty_le": round(score, 2),
            "mau": level
        })

    return results
