STUDENTS_FILE = "QuanLyHocSinh/ultils/students.json"
HEALTH_FILE = "QuanLyHocSinh/ultils/daily_health.json"
MEAL_FILE = "QuanLyHocSinh/ultils/meal_daily.json"
FINANCE_FILE = "QuanLyHocSinh/ultils/fee.json"

import json


def load_data(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy file {file_path}. Trả về list rỗng.")
        return []
    except json.JSONDecodeError:
        print(f"Lỗi: File {file_path} không hợp lệ hoặc bị hỏng. Trả về list rỗng.")
        return []


def save_data(data, file_path):
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Lỗi khi lưu dữ liệu vào {file_path}: {e}")


def load_students():
    return load_data(STUDENTS_FILE)


def save_students(students):
    save_data(students, STUDENTS_FILE)


def load_health_records():
    return load_data(HEALTH_FILE)


def save_health_records(records):
    save_data(records, HEALTH_FILE)


def load_meal_records():
    return load_data(MEAL_FILE)


def save_meal_records(records):
    save_data(records, MEAL_FILE)


import json
from datetime import date, datetime


# Giả định các hàm load_data, load_students, load_health_records, load_financial_records đã tồn tại

# --- CÁC HÀM TÍNH TOÁN STATS CỤ THỂ ---

def load_financial_records():
    return load_data(FINANCE_FILE)




def get_gender_chart_data(students):
    """[DEPRECATED] Đã chuyển sang dao.get_gender_chart_data."""
    from QuanLyHocSinh import dao
    return dao.get_gender_chart_data(students)


def get_revenue_chart_data(financial_records):
    """[DEPRECATED] Đã chuyển sang dao.get_revenue_chart_data."""
    from QuanLyHocSinh import dao
    return dao.get_revenue_chart_data(financial_records)


def get_average_weight_chart_data(all_health_records):
    """[DEPRECATED] Đã chuyển sang dao.get_average_weight_chart_data."""
    from QuanLyHocSinh import dao
    return dao.get_average_weight_chart_data(all_health_records)