# dao.py - Data Access Object Layer
# File này chịu trách nhiệm truy cập và xử lý dữ liệu

from datetime import datetime, date
from QuanLyHocSinh.ultils import ultils
from QuanLyHocSinh import db
from QuanLyHocSinh.model import User, Student, Class, HealthRecord, Invoice, SystemConfig
import hashlib


# ==================== USER FUNCTIONS ====================
def auth_user(username, password):
    """
    Xác thực người dùng với username và password
    """
    password_hash = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
    return User.query.filter(
        User.username == username.strip(),
        User.password == password_hash
    ).first()


def get_user_by_id(user_id):
    """
    Lấy user theo ID
    """
    return User.query.get(user_id)


def add_user(name, username, password, **kwargs):
    """
    Thêm user mới
    """
    password_hash = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
    
    user = User(
        firstName=name.split()[0] if name else '',
        lastName=' '.join(name.split()[1:]) if len(name.split()) > 1 else '',
        username=username.strip(),
        password=password_hash,
        email=kwargs.get('email', f"{username}@example.com"),
        phone=kwargs.get('phone', ''),
        user_role=kwargs.get('user_role')
    )
    
    db.session.add(user)
    db.session.commit()
    
    return user


# ==================== STUDENT FUNCTIONS ====================
def load_students(class_id=None, kw=None, page=1):
    """
    Tải danh sách học sinh từ JSON (hoặc database)
    Hỗ trợ lọc theo class_id, từ khóa tìm kiếm, và phân trang
    """
    # Sử dụng JSON cho demo
    students = ultils.load_students()
    
    # Lọc theo class nếu cần
    if class_id:
        students = [s for s in students if s.get('class_id') == int(class_id)]
    
    # Tìm kiếm theo từ khóa
    if kw:
        kw = kw.lower()
        students = [s for s in students if kw in s.get('name', '').lower()]
    
    # Phân trang (giả định PAGE_SIZE = 10)
    PAGE_SIZE = 10
    start = (page - 1) * PAGE_SIZE
    end = start + PAGE_SIZE
    
    return students[start:end]


def count_students(class_id=None, kw=None):
    """
    Đếm số lượng học sinh
    """
    students = ultils.load_students()
    
    if class_id:
        students = [s for s in students if s.get('class_id') == int(class_id)]
    
    if kw:
        kw = kw.lower()
        students = [s for s in students if kw in s.get('name', '').lower()]
    
    return len(students)


def add_student(student_data):
    """
    Thêm học sinh mới
    """
    students = ultils.load_students()
    new_id = max([s['id'] for s in students], default=0) + 1
    student_data['id'] = new_id
    students.append(student_data)
    ultils.save_students(students)
    return student_data


def update_student(student_id, student_data):
    """
    Cập nhật thông tin học sinh
    """
    students = ultils.load_students()
    for student in students:
        if student['id'] == int(student_id):
            student.update(student_data)
            ultils.save_students(students)
            return student
    return None


def delete_student(student_id):
    """
    Xóa học sinh
    """
    students = ultils.load_students()
    students = [s for s in students if s['id'] != int(student_id)]
    ultils.save_students(students)
    return True


# ==================== HEALTH RECORD FUNCTIONS ====================
def load_health_records(student_id=None, date_filter=None):
    """
    Tải hồ sơ sức khỏe
    """
    records = ultils.load_health_records()
    
    if student_id:
        records = [r for r in records if r.get('student_id') == int(student_id)]
    
    if date_filter:
        records = [r for r in records if r.get('date') == date_filter]
    
    return records


def save_health_record(record_data):
    """
    Lưu hồ sơ sức khỏe mới hoặc cập nhật
    """
    records = ultils.load_health_records()
    
    # Kiểm tra xem đã có bản ghi cho student này trong ngày này chưa
    student_id = record_data.get('student_id')
    record_date = record_data.get('date')
    
    updated = False
    for record in records:
        if record['student_id'] == student_id and record['date'] == record_date:
            # Cập nhật bản ghi hiện có
            record.update(record_data)
            updated = True
            break
    
    if not updated:
        # Thêm bản ghi mới
        records.append(record_data)
    
    ultils.save_health_records(records)
    return record_data


# ==================== MEAL ATTENDANCE FUNCTIONS ====================
def load_meal_records(date_filter=None, student_id=None):
    """
    Tải bản ghi chấm công ăn
    """
    records = ultils.load_meal_records()
    
    if date_filter:
        records = [r for r in records if r.get('date') == date_filter]
    
    if student_id:
        records = [r for r in records if r.get('student_id') == int(student_id)]
    
    return records


def save_meal_record(record_data):
    """
    Lưu bản ghi chấm công ăn
    """
    records = ultils.load_meal_records()
    
    student_id = record_data.get('student_id')
    record_date = record_data.get('date')
    
    updated = False
    for record in records:
        if record['student_id'] == student_id and record['date'] == record_date:
            record.update(record_data)
            updated = True
            break
    
    if not updated:
        records.append(record_data)
    
    ultils.save_meal_records(records)
    return record_data


# ==================== FINANCIAL FUNCTIONS ====================
def load_financial_records():
    """
    Tải hồ sơ tài chính
    """
    return ultils.load_financial_records()


def update_payment_status(student_id, month, paid_status):
    """
    Cập nhật trạng thái thanh toán
    """
    records = ultils.load_financial_records()
    
    for record in records:
        if record.get('student_id') == int(student_id) and record.get('month') == month:
            record['paid_status'] = paid_status
            if paid_status:
                record['payment_date'] = date.today().isoformat()
            ultils.save_data(records, ultils.FINANCE_FILE)
            return record
    
    return None


# ==================== CLASS FUNCTIONS ====================
def load_classes():
    """
    Tải danh sách các lớp
    """
    # Có thể lấy từ database hoặc JSON tùy theo thiết kế
    return Class.query.filter(Class.active == True).all()


def get_class_by_id(class_id):
    """
    Lấy thông tin lớp theo ID
    """
    return Class.query.get(class_id)


# ==================== STATISTICS FUNCTIONS ====================
def get_dashboard_stats(today_str):
    """
    Lấy thống kê cho dashboard
    """
    students = ultils.load_students()
    all_health_records = ultils.load_health_records()
    financial_records = ultils.load_financial_records()
    
    return ultils.get_dashboard_stats(
        students,
        all_health_records,
        financial_records,
        today_str
    )


def get_chart_data():
    """
    Lấy dữ liệu cho các biểu đồ
    """
    students = ultils.load_students()
    financial_records = ultils.load_financial_records()
    health_records = ultils.load_health_records()
    
    return {
        'gender_chart': ultils.get_gender_chart_data(students),
        'revenue_chart': ultils.get_revenue_chart_data(financial_records),
        'weight_chart': ultils.get_average_weight_chart_data(health_records)
    }