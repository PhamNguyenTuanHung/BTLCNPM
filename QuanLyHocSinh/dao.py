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


# ==================== SYSTEM CONFIG FUNCTIONS ====================
def get_system_config(key, default=None):
    """
    Lấy giá trị cấu hình hệ thống theo key
    
    Args:
        key: Tên key cấu hình (vd: 'tuition', 'maxNumber', 'mealFee')
        default: Giá trị mặc định nếu không tìm thấy
    
    Returns:
        Giá trị cấu hình hoặc giá trị mặc định
    """
    config = SystemConfig.query.filter_by(key=key, active=True).first()
    if config:
        return float(config.value)
    return default


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
    Cập nhật thông tin học sinh và thông tin sức khỏe (nếu có)
    """
    try:
        student = Student.query.get(student_id)
        if not student:
            return None
        
        # Cập nhật thông tin cơ bản của học sinh
        if 'firstName' in student_data:
            student.firstName = student_data['firstName']
        if 'lastName' in student_data:
            student.lastName = student_data['lastName']
        if 'parentName' in student_data:
            student.parentName = student_data['parentName']
        if 'parentPhone' in student_data:
            student.parentPhone = student_data['parentPhone']
        if 'guardianRelationship' in student_data:
            student.guardianRelationship = student_data['guardianRelationship']
        if 'gender' in student_data:
            student.gender = student_data['gender']
        if 'birthday' in student_data:
            from datetime import datetime
            if isinstance(student_data['birthday'], str):
                student.birthday = datetime.strptime(student_data['birthday'], '%Y-%m-%d')
            else:
                student.birthday = student_data['birthday']
        
        # Cập nhật thông tin sức khỏe (nếu có)
        if 'weight' in student_data and 'bodyTemperature' in student_data:
            from datetime import datetime
            
            # Tạo bản ghi sức khỏe mới
            health_record = HealthRecord(
                weight=float(student_data['weight']),
                bodyTemperature=float(student_data['bodyTemperature']),
                note=student_data.get('note', ''),
                feverWarning=float(student_data['bodyTemperature']) >= 37.5,
                student_id=student_id,
                recordingDate=datetime.utcnow()
            )
            db.session.add(health_record)
        
        db.session.commit()
        
        # Return student data dưới dạng dict
        return {
            'id': student.id,
            'firstName': student.firstName,
            'lastName': student.lastName,
            'name': f"{student.lastName} {student.firstName}",
            'gender': student.gender,
            'parentName': student.parentName,
            'parentPhone': student.parentPhone,
            'guardianRelationship': student.guardianRelationship
        }
    except Exception as e:
        db.session.rollback()
        print(f"Error updating student: {e}")
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
    # Lấy dữ liệu từ database rồi chuyển sang list dict để tái sử dụng logic cũ
    students_db = Student.query.filter(Student.active == True).all()
    health_db = HealthRecord.query.filter(HealthRecord.active == True).all()
    invoices_db = Invoice.query.filter(Invoice.active == True).all()

    students = []
    for s in students_db:
        students.append({
            'id': s.id,
            'name': f"{s.lastName} {s.firstName}",
            'gender': 'Nam' if s.gender else 'Nữ'
        })

    all_health_records = []
    for r in health_db:
        all_health_records.append({
            'student_id': r.student_id,
            'date': r.recordingDate.date().isoformat(),
            'weight': r.weight,
            'temp': r.bodyTemperature
        })

    financial_records = []
    for inv in invoices_db:
        financial_records.append({
            'student_id': inv.student_id,
            'paid_status': inv.paymentDate is not None
        })

    return get_dashboard_stats_from_lists(
        students,
        all_health_records,
        financial_records,
        today_str
    )


def get_chart_data():
    """
    Lấy dữ liệu cho các biểu đồ
    """
    # Lấy dữ liệu từ database rồi chuyển sang dạng list dict
    students_db = Student.query.filter(Student.active == True).all()
    invoices_db = Invoice.query.filter(Invoice.active == True).all()
    health_db = HealthRecord.query.filter(HealthRecord.active == True).all()

    students = []
    for s in students_db:
        students.append({
            'id': s.id,
            'name': f"{s.lastName} {s.firstName}",
            'gender': 'Nam' if s.gender else 'Nữ'
        })

    financial_records = []
    for inv in invoices_db:
        financial_records.append({
            'student_id': inv.student_id,
            'paid_status': inv.paymentDate is not None
        })

    health_records = []
    for r in health_db:
        health_records.append({
            'student_id': r.student_id,
            'date': r.recordingDate.date().isoformat(),
            'weight': r.weight,
            'temp': r.bodyTemperature
        })

    return {
        'gender_chart': get_gender_chart_data(students),
        'revenue_chart': get_revenue_chart_data(financial_records),
        'weight_chart': get_average_weight_chart_data(health_records)
    }


# ==================== STATISTICS HELPER FUNCTIONS (moved from ultils) ====================

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
    """Tính số lượng trẻ có nhiệt độ cao (>= 37.5°C) trong ngày được chọn."""
    high_risk_count = 0

    records_today = {
        r['student_id']: r
        for r in all_health_records
        if r['date'] == date_to_check
    }

    for student in students:
        record = records_today.get(student['id'])
        if record and record.get('temp') is not None:
            try:
                temp = float(record['temp'])
                if temp >= 37.5:
                    high_risk_count += 1
            except ValueError:
                continue

    return {"high_risk_children": high_risk_count}


def calculate_finance_stats(financial_records):
    """Tính tỷ lệ học phí đã thu trong tháng hiện tại."""
    if not financial_records:
        return {"paid_ratio": "0%"}

    total_invoices = len(financial_records)
    paid_count = sum(1 for record in financial_records if record.get('paid_status') is True)

    paid_ratio_percent = (paid_count / total_invoices) * 100

    return {"paid_ratio": f"{round(paid_ratio_percent)}%"}


def get_dashboard_stats_from_lists(students, all_health_records, financial_records, date_to_check):
    """Tổng hợp các chỉ số thống kê cho Dashboard từ list dict."""
    gender_stats = calculate_gender_stats(students)
    risk_stats = calculate_health_risk_stats(all_health_records, students, date_to_check)
    finance_stats = calculate_finance_stats(financial_records)

    dashboard_stats = {**gender_stats, **risk_stats, **finance_stats}
    dashboard_stats['hoc_phi_co_ban'] = 3000000
    dashboard_stats['tien_an_them_daily'] = 50000
    dashboard_stats['tong_du_kien'] = 15000000

    return dashboard_stats


def get_gender_chart_data(students):
    """Chuẩn bị dữ liệu cho biểu đồ tròn giới tính."""
    male_count = sum(1 for s in students if s.get('gender') == 'Nam')
    female_count = len(students) - male_count

    return {
        'labels': ['Trẻ Nam', 'Trẻ Nữ'],
        'data': [male_count, female_count],
        'colors': ['#5BC0EB', '#FF6B6B']
    }


def get_revenue_chart_data(financial_records):
    """Chuẩn bị dữ liệu cho biểu đồ vòng cung tỷ lệ thanh toán."""
    total_invoices = len(financial_records)
    paid_count = sum(1 for r in financial_records if r.get('paid_status') is True)
    unpaid_count = total_invoices - paid_count

    return {
        'labels': ['Đã thanh toán', 'Chưa thanh toán'],
        'data': [paid_count, unpaid_count],
        'colors': ['#10B981', '#F59E0B']
    }


def get_average_weight_chart_data(all_health_records):
    """Tính toán cân nặng trung bình theo ngày (ví dụ 7 ngày gần nhất)."""
    daily_weights = {}

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
                pass

    sorted_dates = sorted(daily_weights.keys(), reverse=True)[:7]
    sorted_dates.sort()

    labels = []
    data = []
    for d in sorted_dates:
        try:
            date_obj = datetime.strptime(d, '%Y-%m-%d')
            labels.append(date_obj.strftime('%d/%m'))
        except ValueError:
            labels.append(d)

        if daily_weights[d]:
            data.append(round(sum(daily_weights[d]) / len(daily_weights[d]), 2))
        else:
            data.append(None)

    return {
        'labels': labels,
        'data': data,
        'title': "Cân nặng trung bình"
    }