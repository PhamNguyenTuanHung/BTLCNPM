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

def calculate_gender_stats(students):
    """Tính tổng số trẻ, số trẻ Nam và số trẻ Nữ."""
    total = len(students)
    male_count = sum(1 for student in students if student.get('gender') == 'Nam')
    female_count = total - male_count

    return {
        "total_children": total,
        "male_count": male_count,
        "female_count": female_count
    }


def calculate_health_risk_stats(all_health_records, students, date_to_check):
    """
    Tính số lượng trẻ có nhiệt độ cao (>= 37.5°C) trong ngày được chọn.

    Args:
        all_health_records (list): Toàn bộ lịch sử hồ sơ sức khỏe.
        students (list): Danh sách học sinh.
        date_to_check (str): Ngày cần kiểm tra (YYYY-MM-DD).
    """
    high_risk_count = 0

    # 1. Tạo dict bản ghi sức khỏe cho ngày cần kiểm tra
    records_today = {
        r['student_id']: r
        for r in all_health_records
        if r['date'] == date_to_check
    }

    # 2. Đếm số trẻ có nhiệt độ cao
    for student in students:
        record = records_today.get(student['id'])
        if record and record.get('temp') is not None:
            try:
                temp = float(record['temp'])
                if temp >= 37.5:
                    high_risk_count += 1
            except ValueError:
                continue  # Bỏ qua nếu nhiệt độ không phải là số

    return {"high_risk_children": high_risk_count}


def calculate_finance_stats(financial_records):
    """
    Tính tỷ lệ học phí đã thu trong tháng hiện tại (giả định tất cả bản ghi là cùng 1 tháng).
    """
    if not financial_records:
        return {"paid_ratio": "0%"}

    total_invoices = len(financial_records)
    paid_count = sum(1 for record in financial_records if record.get('paid_status') is True)

    paid_ratio_percent = (paid_count / total_invoices) * 100

    return {"paid_ratio": f"{round(paid_ratio_percent)}%"}


# -----------------------------------------------------------
# 4. HÀM TỔNG HỢP STATS CHÍNH
# -----------------------------------------------------------

def get_dashboard_stats(students, all_health_records, financial_records, date_to_check):
    """
    Tổng hợp tất cả các chỉ số thống kê cho Dashboard.
    """

    # Tính toán từng nhóm chỉ số
    gender_stats = calculate_gender_stats(students)
    risk_stats = calculate_health_risk_stats(all_health_records, students, date_to_check)
    finance_stats = calculate_finance_stats(financial_records)

    # Kết hợp các kết quả vào một dict duy nhất
    dashboard_stats = {
        **gender_stats,
        **risk_stats,
        **finance_stats
    }

    # Thêm các hằng số khác (nếu cần)
    dashboard_stats['hoc_phi_co_ban'] = 3000000
    dashboard_stats['tien_an_them_daily'] = 50000
    dashboard_stats['tong_du_kien'] = 15000000

    return dashboard_stats


def load_financial_records():
    return load_data(FINANCE_FILE)




def get_gender_chart_data(students):
    """Chuẩn bị dữ liệu cho biểu đồ tròn giới tính."""
    # Hàm này sử dụng kết quả từ calculate_gender_stats
    male_count = sum(1 for s in students if s.get('gender') == 'Nam')
    female_count = len(students) - male_count

    return {
        'labels': ['Trẻ Nam', 'Trẻ Nữ'],
        'data': [male_count, female_count],
        # Màu sắc nên hài hòa với theme của trang
        'colors': ['#5BC0EB', '#FF6B6B']  # Xanh da trời và Đỏ hồng
    }


# --- 2. Dữ liệu Biểu đồ Doanh thu (Biểu đồ Vòng cung) ---
def get_revenue_chart_data(financial_records):
    """Chuẩn bị dữ liệu cho biểu đồ vòng cung tỷ lệ thanh toán."""
    total_invoices = len(financial_records)
    paid_count = sum(1 for r in financial_records if r.get('paid_status') is True)
    unpaid_count = total_invoices - paid_count

    return {
        'labels': ['Đã thanh toán', 'Chưa thanh toán'],
        'data': [paid_count, unpaid_count],
        # Xanh lá cho Đã thanh toán, Cam/Đỏ cho Chưa thanh toán
        'colors': ['#10B981', '#F59E0B']
    }


# --- 3. Dữ liệu Biểu đồ Cân nặng Trung bình (Biểu đồ Đường) ---
def get_average_weight_chart_data(all_health_records):
    """Tính toán cân nặng trung bình theo ngày (ví dụ 7 ngày gần nhất)."""
    daily_weights = {}  # { 'YYYY-MM-DD': [w1, w2, ...] }

    for record in all_health_records:
        record_date = record['date']
        weight = record.get('weight')
        if weight is not None:
            try:
                weight_val = float(weight)
                if record_date not in daily_weights:
                    daily_weights[record_date] = []
                daily_weights[record_date].append(weight_val)
            except ValueError:
                pass  # Bỏ qua bản ghi lỗi

    # Lấy ra và sắp xếp 7 ngày gần nhất
    sorted_dates = sorted(daily_weights.keys(), reverse=True)[:7]
    sorted_dates.sort()  # Sắp xếp lại từ cũ đến mới

    labels = []
    data = []
    for d in sorted_dates:
        # Định dạng nhãn ngày cho dễ đọc hơn (ví dụ: 25/11)
        try:
            date_obj = datetime.strptime(d, '%Y-%m-%d')
            labels.append(date_obj.strftime('%d/%m'))
        except ValueError:
            labels.append(d)

        # Tính toán giá trị trung bình
        if daily_weights[d]:
            data.append(round(sum(daily_weights[d]) / len(daily_weights[d]), 2))
        else:
            data.append(None)

    return {
        'labels': labels,
        'data': data,
        'title': "Cân nặng trung bình"
    }