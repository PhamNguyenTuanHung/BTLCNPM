# dao.py - Data Access Object Layer
# File này chịu trách nhiệm truy cập và xử lý dữ liệu

import hashlib
from datetime import datetime, date

from QuanLyHocSinh import db
from QuanLyHocSinh.model import User, Student, Class, HealthRecord, Invoice, SystemConfig, MealAttendance
from QuanLyHocSinh.ultils import ultils


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
def load_students(class_id=None, kw=None, page=1, page_size=10):
    """
    Load danh sách học sinh
    - Lọc theo lớp
    - Tìm kiếm theo tên
    - Phân trang
    """
    query = Student.query.filter(Student.active == True)

    if class_id:
        query = query.filter(Student.class_id == int(class_id))

    if kw:
        kw = kw.strip()
        query = query.filter(
            (Student.firstName.ilike(f"%{kw}%")) |
            (Student.lastName.ilike(f"%{kw}%"))
        )

    pagination = query.order_by(Student.id).paginate(
        page=page,
        per_page=page_size,
        error_out=False
    )

    return {
        "students": pagination.items,
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": pagination.page,
        "has_next": pagination.has_next,
        "has_prev": pagination.has_prev
    }




def count_students(class_id=None):
    """
    Đếm số lượng học sinh
    """
    students = ultils.load_students()

    if class_id:
        students = [s for s in students if s.get('class_id') == int(class_id)]

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

def calc_age(birthday):
    today = date.today()
    return today.year - birthday.year - (
        (today.month, today.day) < (birthday.month, birthday.day)
    )

def delete_student(student_id):
    """
    Xóa học sinh
    """
    students = ultils.load_students()
    students = [s for s in students if s['id'] != int(student_id)]
    ultils.save_students(students)
    return True

def build_student_view(
    students,
    health_records=None,
    include_age=False,
    include_gender=False,
    include_parent=False,
    include_phone=False
):
    result = []

    for s in students:
        item = {
            'id': s.id,
            'name': f"{s.lastName} {s.firstName}"
        }

        # Health record
        if health_records is not None:
            record = health_records.get(s.id)
            item['current_record'] = (
                {
                    'weight': record.weight,
                    'temp': record.bodyTemperature,
                    'note': record.note
                } if record else {}
            )

        if include_age:
            item['age'] = f"{calc_age(s.birthday)} tuổi"

        if include_gender:
            item['gender'] = 'Nam' if s.gender else 'Nữ'

        if include_parent:
            item['parent'] = s.parentName

        if include_phone:
            item['phone'] = s.parentPhone

        result.append(item)

    return result


# ==================== HEALTH RECORD FUNCTIONS ====================
from sqlalchemy import or_

def load_students_with_health(
    teacher_id,
    date_filter=None,
    kw=None,
    page=1,
    page_size=10
):
    """
    Lấy danh sách học sinh theo lớp giáo viên
    + hồ sơ sức khỏe theo ngày
    + tìm kiếm (kw)
    + phân trang
    """

    query = (
        db.session.query(Student)
        .join(Class, Student.class_id == Class.id)
        .filter(
            Class.teacher_id == teacher_id,
            Student.active == True
        )
    )

    # 🔍 Search keyword
    if kw:
        keyword = f"%{kw.strip()}%"
        query = query.filter(
            or_(
                Student.firstName.ilike(keyword),
                Student.lastName.ilike(keyword)
            )
        )

    query = query.order_by(Student.id.asc())

    pagination = query.paginate(
        page=page,
        per_page=page_size,
        error_out=False
    )

    students = pagination.items

    # 🩺 Lấy health record theo ngày cho các student trong page
    records_by_student = {}
    if date_filter and students:
        student_ids = [s.id for s in students]

        records = (
            db.session.query(HealthRecord)
            .filter(
                HealthRecord.student_id.in_(student_ids),
                HealthRecord.active == True,
                db.func.date(HealthRecord.recordingDate) == date_filter
            )
            .all()
        )

        records_by_student = {r.student_id: r for r in records}

    return {
        'students': students,
        'records_by_student': records_by_student,
        'pagination': pagination
    }

def get_today_health_records():
    today = date.today()
    records = db.session.query(HealthRecord).filter(
        func.date(HealthRecord.recordingDate) == today
    ).all()

    return {r.student_id: r for r in records}

def count_students_with_health_record(teacher_id, date):
    return (
        db.session.query(HealthRecord.student_id)
        .join(Student)
        .join(Class)
        .filter(
            Class.teacher_id == teacher_id,
            Student.active == True,
            HealthRecord.active == True,
            HealthRecord.weight.isnot(None),
            HealthRecord.bodyTemperature.isnot(None),
            db.func.date(HealthRecord.recordingDate) == date
        )
        .distinct()
        .count()
    )

def build_health_progress_stats(teacher_id, date, total_students):
    recorded_count = count_students_with_health_record(
        teacher_id=teacher_id,
        date=date
    )

    return {
        'completed': recorded_count,
        'total': total_students,
        'percentage': (recorded_count / total_students * 100)
        if total_students else 0
    }

def build_health_student_view(students, records_by_student):
    result = []

    for s in students:
        record = records_by_student.get(s.id)

        current_record = {}
        if record:
            current_record = {
                'weight': record.weight,
                'temp': record.bodyTemperature,
                'note': record.note
            }

        result.append({
            'id': s.id,
            'name': f"{s.lastName} {s.firstName}",
            'current_record': current_record
        })

    return result

def save_health_record(student_id, record_date, weight, temp, note):
    """
    Lưu hồ sơ sức khỏe mới hoặc cập nhật
    record_data: dict với keys = student_id, date, weight, temp, note
    """

    # Tìm bản ghi tồn tại
    if record_date is None:
        record_date = date.today()
    if isinstance(record_date, str):
        record_date = datetime.strptime(record_date, "%Y-%m-%d").date()
    record = HealthRecord.query.filter_by(
        student_id=student_id,
        recordingDate=record_date,
        active=True
    ).first()

    if record:
        # Cập nhật
        record.weight = weight
        record.bodyTemperature = temp
        record.note = note
    else:
        # Tạo mới
        record = HealthRecord(
            student_id=student_id,
            weight=weight,
            bodyTemperature=temp,
            note=note,
            active=True
        )
        db.session.add(record)

    db.session.commit()
    return record


# ==================== MEAL ATTENDANCE FUNCTIONS ====================

def update_meal_attendance(student_id, date, ate_today, teacher_id, commit=True):
    # Chuẩn hoá date
    if isinstance(date, str):
        date = datetime.strptime(date, '%Y-%m-%d').date()

    # Tìm bản ghi theo NGÀY (bỏ giờ)
    record = MealAttendance.query.filter(
        MealAttendance.student_id == student_id,
        func.date(MealAttendance.attendance_date) == date
    ).first()

    if ate_today:
        # ✅ CÓ ĂN → đảm bảo có record
        if not record:
            record = MealAttendance(
                student_id=student_id,
                attendance_date=datetime.combine(date, datetime.min.time()),
                created_by=teacher_id,
                note=None
            )
            db.session.add(record)
    else:
        # ❌ KHÔNG ĂN → xoá record nếu tồn tại
        if record:
            db.session.delete(record)

    if commit:
        db.session.commit()
from sqlalchemy import extract, func

def count_meal_days(student_id, month, year):
    return db.session.query(func.count(MealAttendance.id)).filter(
        MealAttendance.student_id == student_id,
        extract('month', MealAttendance.attendance_date) == month,
        extract('year', MealAttendance.attendance_date) == year
    ).scalar() or 0

def is_ate_today(student_id, date):
    return db.session.query(MealAttendance.id).filter(
        MealAttendance.student_id == student_id,
        func.date(MealAttendance.attendance_date) == date
    ).first() is not None

# ==================== FINANCIAL FUNCTIONS ====================
def load_financial_records(month=None, year=None):
    """
    Tải danh sách hồ sơ tài chính (hóa đơn học phí)
    """

    # Lấy cấu hình hệ thống
    base_tuition = get_system_config('tuition', default=3000000)
    meal_cost_per_day = get_system_config('mealFee', default=50000)

    query = (
        db.session.query(Invoice, Student)
        .join(Student, Student.id == Invoice.student_id)
        .filter(Invoice.active == True)
    )

    # Nếu có lọc theo tháng / năm
    if month:
        query = query.filter(Invoice.month == month)
    if year:
        query = query.filter(Invoice.year == year)

    invoices = query.all()

    financial_records = []

    for inv, student in invoices:
        meal_days = count_meal_days(student.id, month, year)
        tuition_fee = inv.tuition if inv.tuition is not None else base_tuition
        meal_fee = inv.mealFee if inv.mealFee is not None else meal_cost_per_day

        total_meal_cost = meal_days * meal_fee
        calculated_total = tuition_fee + total_meal_cost

        financial_records.append({
            'invoice_id': inv.id,
            'student_id': student.id,
            'student_name': f"{student.lastName} {student.firstName}",
            'parent_name': student.parentName,
            'month': inv.month,
            'year': inv.year,
            'tuition_fee': tuition_fee,
            'meal_days': meal_days,
            'meal_fee_per_day': meal_fee,
            'total_meal_cost': total_meal_cost,
            'total_amount': inv.total if inv.total is not None else calculated_total,
            'is_paid': inv.paymentDate is not None,
            'payment_date': inv.paymentDate
        })

    return financial_records

def is_invoice_paid(student_id, month, year):
    invoice = Invoice.query.filter_by(
        student_id=student_id,
        month=month,
        year=year,
        active=True
    ).first()

    if not invoice:
        return False

    return invoice.paymentDate is not None

def update_invoice_payment(student_id, month, year):
    invoice = Invoice.query.filter_by(
        student_id=student_id,
        month=month,
        year=year,
        active=True
    ).first()

    if not invoice:
        return False

    if invoice.paymentDate:
        return "Đã đóng rồi"

    invoice.paymentDate = datetime.utcnow()
    db.session.commit()
    return True

def pay_invoice(invoice_id):
    """
    Thanh toán hóa đơn theo invoice_id.
    Trả về dict {'success': bool, 'message': str} và status code nếu cần.
    """
    # Lấy hóa đơn (cách mới với SQLAlchemy 2.x)
    invoice = db.session.get(Invoice, invoice_id)

    if not invoice:
        return {
            'success': False,
            'message': 'Không tìm thấy hóa đơn'
        }, 404

    if invoice.paymentDate:
        return {
            'success': False,
            'message': 'Hóa đơn đã được thanh toán'
        }, 400

    # ===== THANH TOÁN =====
    invoice.paymentDate = datetime.now()
    invoice.is_paid = True  # nếu có field này
    db.session.commit()

    return {
        'success': True,
        'message': 'Thanh toán hóa đơn thành công'
    }, 200

def generate_monthly_invoices(tuition, meal_fee):
    now = datetime.now()
    month = now.month
    year = now.year

    students = Student.query.filter_by(active=True).all()

    for s in students:
        exists = Invoice.query.filter_by(
            student_id=s.id,
            month=month,
            year=year
        ).first()

        if exists:
            continue  # đã có rồi thì bỏ qua

        invoice = Invoice(
            student_id=s.id,
            teacher_id=s.class_.teacher_id if s.class_ else None,
            month=month,
            year=year,
            tuition=tuition,
            mealDays=0,
            mealFee=meal_fee,
            total=tuition,
            paymentDate=None
        )

        db.session.add(invoice)

    db.session.commit()


# ==================== CLASS FUNCTIONS ====================
def load_classes():
    """
    Tải danh sách các lớp
    """
    # Có thể lấy từ database hoặc JSON tùy theo thiết kế
    return Class.query.filter(Class.active == True).all()

def get_teacher_class_info(teacher_id):
    teacher_class = get_class_by_teacher_id(teacher_id=teacher_id)

    if not teacher_class:
        return None, 0

    current_count = get_current_student_count(class_id=teacher_class.id)
    return teacher_class.id, current_count

def get_class_by_teacher_id(teacher_id):
    """
    Lấy thông tin lớp theo id giáo viên
    """
    return Class.query.filter(Class.teacher_id == teacher_id).first()

def get_class_by_id(class_id):
    """
    Lấy thông tin lớp theo ID
    """
    return Class.query.get(class_id)

def get_current_student_count(class_id):
    return Student.query.filter(
        Student.class_id == class_id,
        Student.active == True
    ).count()


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
