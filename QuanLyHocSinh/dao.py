# dao.py - Data Access Object Layer
# File này chịu trách nhiệm truy cập và xử lý dữ liệu

import hashlib
from datetime import datetime, date
from functools import wraps
from flask_login import current_user
from flask import redirect, abort

from QuanLyHocSinh import db
from QuanLyHocSinh.model import User, Student, Class, HealthRecord, Invoice, SystemConfig, MealAttendance
from sqlalchemy import or_, extract, func


# ==================== HELPER FUNCTIONS ====================

def paginate(query, page=1, page_size=10):
    """
    Generic pagination helper
    """
    page = max(1, page)
    page_size = max(1, page_size)
    
    total = query.count()
    items = query.limit(page_size).offset((page - 1) * page_size).all()
    
    return {
        'items': items,
        'total': total,
        'page': page,
        'page_size': page_size,
        'total_pages': (total + page_size - 1) // page_size if total > 0 else 1
    }

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
    if not config or config.value is None:
        return default

    value = config.value

    # Nếu default có kiểu → ép theo kiểu đó
    if default is not None:
        try:
            return type(default)(value)
        except ValueError:
            return default

    return value


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
                    'note': record.note,
                    'date': record.recordingDate  # Add date field for display
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
        updated_status=None,  # new: "updated" / "not_updated"
        page=1,
        page_size=10
):
    """
    Lấy danh sách học sinh theo lớp giáo viên
    + hồ sơ sức khỏe theo ngày (date_filter)
    + tìm kiếm (kw)
    + filter theo trạng thái đã cập nhật/not cập nhật
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

    # Search keyword
    if kw:
        keyword = f"%{kw.strip()}%"
        query = query.filter(
            or_(
                Student.firstName.ilike(keyword),
                Student.lastName.ilike(keyword),
                Student.parentName.ilike(keyword)
            )
        )

    query = query.order_by(Student.id.asc())

    pagination = query.paginate(
        page=page,
        per_page=page_size,
        error_out=False
    )

    students = pagination.items

    # Lấy health record theo ngày
    records_by_student = {}
    updated_on_day = set()

    if students and date_filter:
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
        updated_on_day = {r.student_id for r in records}

        # Filter theo updated_status
        if updated_status == "updated":
            students = [s for s in students if s.id in updated_on_day]
        elif updated_status == "not_updated":
            students = [s for s in students if s.id not in updated_on_day]

    return {
        'students': students,
        'records_by_student': records_by_student,
        'updated_on_day': updated_on_day,
        'pagination': pagination
    }



def get_latest_health_records(student_ids=None):
    """
    Lấy bản ghi sức khỏe MỚI NHẤT của mỗi học sinh
    (thay vì chỉ lấy hôm nay)
    
    Args:
        student_ids: Optional list of student IDs to filter
    Returns:
        Dict {student_id: HealthRecord}
    """
    from sqlalchemy import func
    
    # Subquery: Lấy ngày ghi nhận mới nhất cho mỗi học sinh
    latest_dates = (
        db.session.query(
            HealthRecord.student_id,
            func.max(HealthRecord.recordingDate).label('max_date')
        )
        .filter(HealthRecord.active == True)
    )
    
    if student_ids:
        latest_dates = latest_dates.filter(HealthRecord.student_id.in_(student_ids))
    
    latest_dates = latest_dates.group_by(HealthRecord.student_id).subquery()
    
    # Join để lấy bản ghi đầy đủ
    records = (
        db.session.query(HealthRecord)
        .join(
            latest_dates,
            db.and_(
                HealthRecord.student_id == latest_dates.c.student_id,
                HealthRecord.recordingDate == latest_dates.c.max_date
            )
        )
        .filter(HealthRecord.active == True)
        .all()
    )
    
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

def update_meal_attendance(student_id, date, ate_today, teacher_id, note=None, commit=True):
    # Chuẩn hoá date
    if isinstance(date, str):
        date = datetime.strptime(date, '%Y-%m-%d').date()

    # Tìm bản ghi theo NGÀY (bỏ giờ)
    record = MealAttendance.query.filter(
        MealAttendance.student_id == student_id,
        func.date(MealAttendance.attendance_date) == date
    ).first()

    if ate_today:
        # CÓ ĂN → đảm bảo có record
        if not record:
            record = MealAttendance(
                student_id=student_id,
                attendance_date=datetime.combine(date, datetime.min.time()),
                created_by=teacher_id,
                note=note
            )
            db.session.add(record)
        else:
            # Cập nhật note nếu record đã tồn tại
            record.note = note
    else:
        # KHÔNG ĂN → xoá record nếu tồn tại
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


def get_meal_dates(student_id, month, year):
    """
    Lấy danh sách các ngày mà học sinh đã ăn trong tháng
    
    Args:
        student_id: ID của học sinh
        month: Tháng
        year: Năm
        
    Returns:
        List of date objects
    """
    records = db.session.query(MealAttendance.attendance_date).filter(
        MealAttendance.student_id == student_id,
        extract('month', MealAttendance.attendance_date) == month,
        extract('year', MealAttendance.attendance_date) == year
    ).order_by(MealAttendance.attendance_date.asc()).all()
    
    return [r[0].date() for r in records]




def get_week_dates(week_offset=0):
    """
    Lấy danh sách các ngày trong tuần (Thứ 2 -> Chủ nhật)
    
    Args:
        week_offset: 0 = tuần hiện tại, -1 = tuần trước, +1 = tuần sau
        
    Returns:
        List of date objects [Mon, Tue, Wed, Thu, Fri, Sat, Sun]
    """
    from datetime import timedelta
    
    today = date.today()
    # Calculate Monday of current week (weekday() returns 0=Mon, 6=Sun)
    monday = today - timedelta(days=today.weekday())
    
    # Add week offset
    monday = monday + timedelta(weeks=week_offset)
    
    # Generate 7 days starting from Monday
    return [monday + timedelta(days=i) for i in range(7)]


def get_weekly_meal_attendance(student_ids, week_dates):
    """
    Trả về:
    {
        student_id: {
            'YYYY-MM-DD': {
                'attended': bool,
                'note': str
            }
        }
    }
    """
    if not student_ids or not week_dates:
        return {}

    start_date = week_dates[0]
    end_date = week_dates[-1]

    records = db.session.query(MealAttendance).filter(
        MealAttendance.student_id.in_(student_ids),
        func.date(MealAttendance.attendance_date) >= start_date,
        func.date(MealAttendance.attendance_date) <= end_date
    ).all()

    # Init mặc định
    result = {}
    for student_id in student_ids:
        result[student_id] = {}
        for day in week_dates:
            result[student_id][day.isoformat()] = {
                'attended': False,
                'note': ''
            }

    # Ghi đè từ DB
    for record in records:
        student_id = record.student_id
        date_str = record.attendance_date.date().isoformat()

        if student_id in result and date_str in result[student_id]:
            result[student_id][date_str]['attended'] = True
            result[student_id][date_str]['note'] = record.note or ''

    return result


def save_weekly_meal_attendance(attendance_data, teacher_id):
    """
    Lưu dữ liệu điểm danh bữa ăn cho cả tuần
    
    Args:
        attendance_data: List of dicts [{student_id, date, ate, note (optional)}]
        teacher_id: ID của giáo viên tạo bản ghi
    """
    for item in attendance_data:
        student_id = item['student_id']
        date_str = item['date']
        ate = item['ate']
        note = item.get('note', '')
        
        update_meal_attendance(
            student_id=student_id,
            date=date_str,
            ate_today=ate,
            teacher_id=teacher_id,
            note=note,
            commit=False
        )
    
    db.session.commit()


def export_meal_attendance_excel(student_ids, month, year, class_name=""):
    """
    Xuất dữ liệu điểm danh ăn ra file Excel với định dạng đẹp
    
    Args:
        student_ids: List of student IDs
        month: Tháng
        year: Năm
        class_name: Tên lớp (optional)
    
    Returns:
        File path of generated Excel file
    """
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    from datetime import datetime, timedelta
    import calendar
    import os
    
    # Create workbook
    wb = Workbook()
    ws = wb.active
    ws.title = f"Điểm danh tháng {month}"
    
    # Get number of days in month
    num_days = calendar.monthrange(year, month)[1]
    
    # Get student data
    students = Student.query.filter(Student.id.in_(student_ids)).order_by(Student.id).all()
    
    # Get all attendance data for the month
    start_date = datetime(year, month, 1).date()
    end_date = datetime(year, month, num_days).date()
    
    attendance_records = db.session.query(MealAttendance).filter(
        MealAttendance.student_id.in_(student_ids),
        func.date(MealAttendance.attendance_date) >= start_date,
        func.date(MealAttendance.attendance_date) <= end_date
    ).all()
    
    # Build attendance dict
    attendance_dict = {}
    for record in attendance_records:
        student_id = record.student_id
        day = record.attendance_date.day
        if student_id not in attendance_dict:
            attendance_dict[student_id] = set()
        attendance_dict[student_id].add(day)
    
    # Styling
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=11)
    center_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # Title
    title_text = f"BẢNG ĐIỂM DANH BỮA ĂN THÁNG {month}/{year}"
    if class_name:
        title_text += f" - {class_name}"
    ws.merge_cells(f'A1:{get_column_letter(num_days + 3)}1')
    title_cell = ws['A1']
    title_cell.value = title_text
    title_cell.font = Font(bold=True, size=14, color="FFFFFF")
    title_cell.fill = PatternFill(start_color="203864", end_color="203864", fill_type="solid")
    title_cell.alignment = center_alignment
    ws.row_dimensions[1].height = 25
    
    # Headers - Row 2: STT and Student Name
    ws['A2'] = "STT"
    ws['B2'] = "Họ và tên"
    
    # Merge STT and Name cells for rows 2-3
    ws.merge_cells('A2:A3')
    ws.merge_cells('B2:B3')
    
    # Day numbers - Row 2
    for day in range(1, num_days + 1):
        col = get_column_letter(day + 2)
        ws[f'{col}2'] = day
        ws[f'{col}2'].font = header_font
        ws[f'{col}2'].fill = header_fill
        ws[f'{col}2'].alignment = center_alignment
        ws[f'{col}2'].border = thin_border
        ws.column_dimensions[col].width = 4
    
    # Day of week - Row 3
    day_names_short = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN']
    thick_border_right = Border(
        left=Side(style='thin'),
        right=Side(style='medium'),  # Thick border on right
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    for day in range(1, num_days + 1):
        col = get_column_letter(day + 2)
        date_obj = datetime(year, month, day).date()
        weekday = date_obj.weekday()  # 0=Monday, 6=Sunday
        ws[f'{col}3'] = day_names_short[weekday]
        ws[f'{col}3'].font = Font(bold=True, color="FFFFFF", size=9)
        ws[f'{col}3'].fill = PatternFill(start_color="5B9BD5", end_color="5B9BD5", fill_type="solid")
        ws[f'{col}3'].alignment = center_alignment
        
        # Add thick border on Sunday to separate weeks
        if weekday == 6:  # Sunday
            ws[f'{col}2'].border = thick_border_right
            ws[f'{col}3'].border = thick_border_right
        else:
            ws[f'{col}3'].border = thin_border
    
    # Total column
    total_col = get_column_letter(num_days + 3)
    ws.merge_cells(f'{total_col}2:{total_col}3')
    ws[f'{total_col}2'] = "Tổng"
    ws[f'{total_col}2'].font = header_font
    ws[f'{total_col}2'].fill = header_fill
    ws[f'{total_col}2'].alignment = center_alignment
    ws[f'{total_col}2'].border = thin_border
    ws.column_dimensions[total_col].width = 8
    
    # Header columns styling
    ws['A2'].font = header_font
    ws['A2'].fill = header_fill
    ws['A2'].alignment = center_alignment
    ws['A2'].border = thin_border    
    ws.column_dimensions['A'].width = 6
    
    ws['B2'].font = header_font
    ws['B2'].fill = header_fill
    ws['B2'].alignment = center_alignment
    ws['B2'].border = thin_border
    ws.column_dimensions['B'].width = 25
    
    ws.row_dimensions[2].height = 20
    ws.row_dimensions[3].height = 18
    
    # Student data (starting from row 4)
    for idx, student in enumerate(students, start=1):
        row = idx + 3  # Start from row 4
        
        # STT
        ws[f'A{row}'] = idx
        ws[f'A{row}'].alignment = center_alignment
        ws[f'A{row}'].border = thin_border
        
        # Student name
        student_name = f"{student.lastName} {student.firstName}"
        ws[f'B{row}'] = student_name
        ws[f'B{row}'].alignment = Alignment(horizontal="left", vertical="center")
        ws[f'B{row}'].border = thin_border
        
        # Attendance days
        student_attendance = attendance_dict.get(student.id, set())
        total_days = 0
        
        for day in range(1, num_days + 1):
            col = get_column_letter(day + 2)
            date_obj = datetime(year, month, day).date()
            weekday = date_obj.weekday()
            
            if day in student_attendance:
                ws[f'{col}{row}'] = "✓"
                ws[f'{col}{row}'].font = Font(color="00B050", bold=True, size=12)
                total_days += 1
            else:
                ws[f'{col}{row}'] = ""
            
            ws[f'{col}{row}'].alignment = center_alignment
            
            # Add thick border on Sunday to separate weeks
            if weekday == 6:  # Sunday
                ws[f'{col}{row}'].border = thick_border_right
            else:
                ws[f'{col}{row}'].border = thin_border
        
        # Total
        ws[f'{total_col}{row}'] = total_days
        ws[f'{total_col}{row}'].alignment = center_alignment
        ws[f'{total_col}{row}'].border = thin_border
        ws[f'{total_col}{row}'].font = Font(bold=True)
        
        ws.row_dimensions[row].height = 18
    
    # Return as BytesIO instead of saving to disk
    from io import BytesIO
    
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    return output


def export_tuition_report_excel(financial_records, month, year, class_name=""):
    """
    Xuất báo cáo chi phí học phí ra file Excel
    
    Args:
        financial_records: List of financial record dicts
        month: Tháng
        year: Năm
        class_name: Tên lớp (optional)
    
    Returns:
        File path of generated Excel file
    """
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    import os
    
    # Create workbook
    wb = Workbook()
    ws = wb.active
    ws.title = f"Chi phí tháng {month}"
    
    # Styling
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=11)
    center_alignment = Alignment(horizontal="center", vertical="center")
    right_alignment = Alignment(horizontal="right", vertical="center")
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # Title
    title_text = f"BÁO CÁO CHI PHÍ HỌC PHÍ THÁNG {month}/{year}"
    if class_name:
        title_text += f" - {class_name}"
    ws.merge_cells('A1:H1')
    title_cell = ws['A1']
    title_cell.value = title_text
    title_cell.font = Font(bold=True, size=14, color="FFFFFF")
    title_cell.fill = PatternFill(start_color="203864", end_color="203864", fill_type="solid")
    title_cell.alignment = center_alignment
    ws.row_dimensions[1].height = 25
    
    # Headers
    headers = ["STT", "Tên học sinh", "Phụ huynh", "Học phí", "Số ngày ăn", "Chi phí ăn", "Tổng cộng", "Trạng thái"]
    for col_num, header in enumerate(headers, start=1):
        cell = ws.cell(row=2, column=col_num)
        cell.value = header
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_alignment
        cell.border = thin_border
    
    # Column widths
    ws.column_dimensions['A'].width = 6
    ws.column_dimensions['B'].width = 25
    ws.column_dimensions['C'].width = 20
    ws.column_dimensions['D'].width = 15
    ws.column_dimensions['E'].width = 12
    ws.column_dimensions['F'].width = 15
    ws.column_dimensions['G'].width = 15
    ws.column_dimensions['H'].width = 15
    ws.row_dimensions[2].height = 20
    
    # Data rows
    total_tuition = 0
    total_meal = 0
    total_all = 0
    paid_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
    unpaid_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
    
    for idx, record in enumerate(financial_records, start=1):
        row = idx + 2
        
        # STT
        ws[f'A{row}'] = idx
        ws[f'A{row}'].alignment = center_alignment
        ws[f'A{row}'].border = thin_border
        
        # Student name
        ws[f'B{row}'] = record['student_name']
        ws[f'B{row}'].alignment = Alignment(horizontal="left", vertical="center")
        ws[f'B{row}'].border = thin_border
        
        # Parent name
        ws[f'C{row}'] = record['parent_name']
        ws[f'C{row}'].alignment = Alignment(horizontal="left", vertical="center")
        ws[f'C{row}'].border = thin_border
        
        # Tuition
        ws[f'D{row}'] = record['tuition_fee']
        ws[f'D{row}'].alignment = right_alignment
        ws[f'D{row}'].border = thin_border
        ws[f'D{row}'].number_format = '#,##0'
        
        # Meal days
        ws[f'E{row}'] = record['meal_days']
        ws[f'E{row}'].alignment = center_alignment
        ws[f'E{row}'].border = thin_border
        
        # Meal cost
        ws[f'F{row}'] = record['total_meal_cost']
        ws[f'F{row}'].alignment = right_alignment
        ws[f'F{row}'].border = thin_border
        ws[f'F{row}'].number_format = '#,##0'
        
        # Total
        ws[f'G{row}'] = record['total_amount']
        ws[f'G{row}'].alignment = right_alignment
        ws[f'G{row}'].border = thin_border
        ws[f'G{row}'].number_format = '#,##0'
        ws[f'G{row}'].font = Font(bold=True)
        
        # Status
        status_text = "Đã đóng" if record['is_paid'] else "Chưa đóng"
        ws[f'H{row}'] = status_text
        ws[f'H{row}'].alignment = center_alignment
        ws[f'H{row}'].border = thin_border
        ws[f'H{row}'].font = Font(bold=True)
        if record['is_paid']:
            ws[f'H{row}'].fill = paid_fill
        else:
            ws[f'H{row}'].fill = unpaid_fill
        
        # Accumulate totals
        total_tuition += record['tuition_fee']
        total_meal += record['total_meal_cost']
        total_all += record['total_amount']
        
        ws.row_dimensions[row].height = 18
    
    # Total row
    total_row = len(financial_records) + 3
    ws.merge_cells(f'A{total_row}:C{total_row}')
    ws[f'A{total_row}'] = "TỔNG CỘNG"
    ws[f'A{total_row}'].font = Font(bold=True, size=12)
    ws[f'A{total_row}'].alignment = center_alignment
    ws[f'A{total_row}'].border = thin_border
    ws[f'A{total_row}'].fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
    
    ws[f'D{total_row}'] = total_tuition
    ws[f'D{total_row}'].font = Font(bold=True, size=11)
    ws[f'D{total_row}'].alignment = right_alignment
    ws[f'D{total_row}'].border = thin_border
    ws[f'D{total_row}'].number_format = '#,##0'
    ws[f'D{total_row}'].fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
    
    ws[f'E{total_row}'] = ""
    ws[f'E{total_row}'].border = thin_border
    ws[f'E{total_row}'].fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
    
    ws[f'F{total_row}'] = total_meal
    ws[f'F{total_row}'].font = Font(bold=True, size=11)
    ws[f'F{total_row}'].alignment = right_alignment
    ws[f'F{total_row}'].border = thin_border
    ws[f'F{total_row}'].number_format = '#,##0'
    ws[f'F{total_row}'].fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
    
    ws[f'G{total_row}'] = total_all
    ws[f'G{total_row}'].font = Font(bold=True, size=12, color="FF0000")
    ws[f'G{total_row}'].alignment = right_alignment
    ws[f'G{total_row}'].border = thin_border
    ws[f'G{total_row}'].number_format = '#,##0'
    ws[f'G{total_row}'].fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
    
    ws[f'H{total_row}'] = ""
    ws[f'H{total_row}'].border = thin_border
    ws[f'H{total_row}'].fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
    
    ws.row_dimensions[total_row].height = 22
    
    # Return as BytesIO instead of saving to disk
    from io import BytesIO
    
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    return output




# ==================== FINANCIAL FUNCTIONS ====================
def load_financial_records(month=None, year=None, keyword=None, class_id=None):
    """
    Tải danh sách học sinh và học phí
    - Hiển thị TẤT CẢ học sinh
    - Meal days lấy từ meal_attendance
    - Invoice chỉ tồn tại khi đã thu tiền
    """
    from datetime import date as datetime_date

    base_tuition = get_system_config('tuition', default=1500000)
    meal_cost_per_day = get_system_config('mealFee', default=30000)

    today = datetime_date.today()
    month = month or today.month
    year = year or today.year

    query = Student.query.filter(Student.active.is_(True))

    if class_id:
        query = query.filter(Student.class_id == class_id)

    students = query.all()
    financial_records = []

    for student in students:
        # Filter theo tên
        if keyword:
            kw = keyword.lower()
            full_name = f"{student.lastName} {student.firstName}".lower()
            if kw not in full_name:
                continue

        # Số bữa ăn
        meal_days = count_meal_days(student.id, month, year)

        # Tính tiền
        tuition_fee = base_tuition
        total_meal_cost = meal_days * meal_cost_per_day
        total_amount = tuition_fee + total_meal_cost

        # Invoice = đã thu tiền
        invoice = Invoice.query.filter_by(
            student_id=student.id,
            month=month,
            year=year,
            active=True
        ).first()

        financial_records.append({
            'invoice_id': invoice.id if invoice else None,
            'student_id': student.id,
            'student_name': f"{student.lastName} {student.firstName}",
            'parent_name': student.parentName,
            'month': month,
            'year': year,
            'tuition_fee': tuition_fee,
            'meal_days': meal_days,
            'meal_fee_per_day': meal_cost_per_day,
            'total_meal_cost': total_meal_cost,
            'total_amount': total_amount,
            'payment_date': invoice.paymentDate if invoice else None
        })

    return financial_records

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
    db.session.commit()

    return {
        'success': True,
        'message': 'Thanh toán hóa đơn thành công'
    }, 200


def get_invoice_data(invoice_id):
    invoice = Invoice.query.get(invoice_id)

    if not invoice:
        return None

    student = invoice.student  # dùng relationship

    # normalize dữ liệu (tránh None trong template)
    invoice.tuition = invoice.tuition or 0
    invoice.mealFee = invoice.mealFee or 0
    invoice.mealDays = invoice.mealDays or 0
    invoice.total = invoice.total or (
            invoice.tuition + invoice.mealFee
    )

    return {
        "student": student,
        "invoice": invoice
    }


# ==================== CLASS FUNCTIONS ====================


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

# ==================== STATISTICS FUNCTIONS ====================

def get_class_enrollment_stats():
    """
    Lấy thống kê sĩ số từng lớp
    Returns: List of {class_name, student_count}
    """
    from sqlalchemy import func
    
    results = db.session.query(
        Class.name,
        func.count(Student.id).label('count')
    ).join(
        Student, Class.id == Student.class_id, isouter=True
    ).filter(
        Class.active == True
    ).group_by(Class.id, Class.name).order_by(Class.name).all()
    
    return [{'class_name': name, 'student_count': count} for name, count in results]


def get_monthly_revenue_stats(start_month=None, end_month=None, year=None):
    """
    Lấy thống kê doanh thu theo tháng
    Args:
        start_month: Tháng bắt đầu (1-12)
        end_month: Tháng kết thúc (1-12)
        year: Năm (default: năm hiện tại)
    Returns: List of {month, year, revenue}
    """
    from datetime import date as dt
    from sqlalchemy import func
    
    if not year:
        year = dt.today().year
    
    # Initialize all months with 0 revenue
    all_months = []
    start = start_month if start_month else 1
    end = end_month if end_month else 12
    
    for month in range(start, end + 1):
        all_months.append({'month': month, 'year': year, 'revenue': 0})
    
   # Get actual revenue data (only from paid invoices)
    query = db.session.query(
        Invoice.month,
        Invoice.year,
        func.sum(Invoice.total).label('revenue')
    ).filter(
        Invoice.active == True,
        Invoice.year == year,
        Invoice.paymentDate.isnot(None)  # Chỉ tính đã thanh toán
    )
    
    if start_month:
        query = query.filter(Invoice.month >= start_month)
    if end_month:
        query = query.filter(Invoice.month <= end_month)
    
    results = query.group_by(Invoice.month, Invoice.year).order_by(Invoice.month).all()
    
    # Update months with actual data
    revenue_dict = {m: float(r or 0) for m, y, r in results}
    for item in all_months:
        if item['month'] in revenue_dict:
            item['revenue'] = revenue_dict[item['month']]
    
    return all_months
