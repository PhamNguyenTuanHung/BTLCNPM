# index.py - Main Application Routes
# File này khởi tạo Flask app và định nghĩa các route chính

from datetime import datetime, date
from flask import render_template, request, redirect, jsonify, session, send_file, abort
from flask_login import login_user, logout_user, current_user, login_required
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO
from QuanLyHocSinh.dao import get_invoice_data

from QuanLyHocSinh import app, dao, login as login_manager, db
from QuanLyHocSinh.ultils import ultils
from QuanLyHocSinh.model import Student, HealthRecord, Invoice, SystemConfig
import math

# Import admin để khởi tạo Flask-Admin
from QuanLyHocSinh import admin


# ==================== USER LOADER ====================
@login_manager.user_loader
def load_user(user_id):
    """
    Flask-Login user loader
    """
    return dao.get_user_by_id(user_id)


# ==================== AUTHENTICATION ROUTES ====================
@app.route('/login')
def login_view():
    """
    Hiển thị trang đăng nhập
    """
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login_process():
    """
    Xử lý đăng nhập và redirect theo role
    """
    username = request.form.get('username')
    password = request.form.get('password')
    
    user = dao.auth_user(username=username, password=password)
    if user:
        login_user(user=user)
        
        # Kiểm tra role và redirect tương ứng
        from QuanLyHocSinh.model import UserRole
        
        # Nếu có tham số next, ưu tiên redirect theo next
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        
        # Redirect theo role
        if user.user_role == UserRole.ADMIN:
            return redirect('/admin')
        else:  # TEACHER hoặc role khác
            return redirect('/')
    
    # Nếu đăng nhập thất bại, quay về trang login với thông báo lỗi
    return render_template('login.html', error='Tên đăng nhập hoặc mật khẩu không đúng!')


@app.route('/register')
def register_view():
    """
    Hiển thị trang đăng ký
    """
    return render_template('register.html')


@app.route('/register', methods=['POST'])
def register_process():
    """
    Xử lý đăng ký người dùng mới
    """
    data = request.form
    
    password = data.get('password')
    confirm = data.get('confirm')
    
    if password != confirm:
        err_msg = 'Mật khẩu không khớp!'
        return render_template('register.html', err_msg=err_msg)
    
    try:
        dao.add_user(
            name=data.get('name'),
            username=data.get('username'),
            password=password,
            email=data.get('email')
        )
        return redirect('/login')
    except Exception as ex:
        return render_template('register.html', err_msg=str(ex))


@app.route('/logout')
def logout_process():
    """
    Đăng xuất
    """
    logout_user()
    return redirect('/login')


# ==================== STUDENT MANAGEMENT ROUTES ====================
@app.route('/')
@app.route('/students')
@login_required
def students_page():
    """
    Trang quản lý học sinh
    """
    # 1. Khởi tạo ngày tháng
    today_str = date.today().isoformat()

    # 2. Lấy danh sách học sinh từ database
    students = Student.query.filter(Student.active == True).all()

    # 3. Lấy bản ghi sức khỏe mới nhất cho mỗi học sinh
    sub = (
        db.session.query(
            HealthRecord.student_id,
            db.func.max(HealthRecord.recordingDate).label('max_date')
        )
        .group_by(HealthRecord.student_id)
        .subquery()
    )

    latest_records = (
        db.session.query(HealthRecord)
        .join(
            sub,
            db.and_(
                HealthRecord.student_id == sub.c.student_id,
                HealthRecord.recordingDate == sub.c.max_date
            )
        )
        .all()
    )

    latest_by_student = {r.student_id: r for r in latest_records}

    def calc_age(birthday):
        today = date.today()
        return today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))

    # 4. Chuẩn hóa dữ liệu theo format cũ để template dùng lại
    students_optimized = []
    for s in students:
        record = latest_by_student.get(s.id)
        current_record = {}
        if record:
            current_record = {
                'weight': record.weight,
                'temp': record.bodyTemperature,
                'note': record.note
            }

        students_optimized.append({
            'id': s.id,
            'name': f"{s.lastName} {s.firstName}",
            'age': f"{calc_age(s.birthday)} tuổi",
            'gender': 'Nam' if s.gender else 'Nữ',
            'parent': s.parentName,
            'phone': s.parentPhone,
            'current_record': current_record
        })

    # 5. Lấy sĩ số tối đa từ cấu hình hệ thống (nếu có)
    max_capacity = int(dao.get_system_config('maxNumber', default=len(students_optimized)))

    return render_template(
        "student.html",
        students=students_optimized,
        today=today_str,
        max_capacity=max_capacity
    )


@app.route("/students", methods=["POST"])
def add_student():
    """
    API thêm học sinh mới
    """
    new_student = request.json
    result = dao.add_student(new_student)
    return jsonify({"success": True, "student": result})


@app.route("/students", methods=["PUT"])
def update_student():
    """
    API cập nhật thông tin học sinh
    """
    updated = request.get_json()
    student_id = updated.get('id')
    
    result = dao.update_student(student_id, updated)
    
    if result:
        return jsonify({"success": True, "student": result})
    return jsonify({"success": False, "message": "Student not found"})


# ==================== HEALTH MANAGEMENT ROUTES ====================
@app.route('/health-management')
def health_management():
    """
    Trang quản lý sức khỏe
    """
    # 1. Xử lý ngày tháng
    today_date = date.today()
    today_str = today_date.isoformat()
    date_str_from_request = request.args.get('date')

    selected_date = today_date
    if date_str_from_request:
        try:
            selected_date = datetime.strptime(date_str_from_request, '%Y-%m-%d').date()
        except ValueError:
            pass

    selected_date_str = selected_date.isoformat()

    # 2. Lấy dữ liệu học sinh và hồ sơ sức khỏe từ database
    students = Student.query.filter(Student.active == True).all()

    records_for_selected_date = (
        db.session.query(HealthRecord)
        .filter(db.func.date(HealthRecord.recordingDate) == selected_date_str)
        .all()
    )

    records_by_student = {r.student_id: r for r in records_for_selected_date}

    students_optimized = []
    recorded_count = 0

    for s in students:
        record = records_by_student.get(s.id)
        current_record = {}
        if record:
            current_record = {
                'weight': record.weight,
                'temp': record.bodyTemperature,
                'note': record.note
            }
            if record.weight is not None and record.bodyTemperature is not None:
                recorded_count += 1

        students_optimized.append({
            'id': s.id,
            'name': f"{s.lastName} {s.firstName}",
            'current_record': current_record
        })

    # 4. Tính toán tiến độ
    total_students = len(students_optimized)
    progress_stats = {
        'completed': recorded_count,
        'total': total_students,
        'percentage': (recorded_count / total_students) * 100 if total_students > 0 else 0
    }

    return render_template(
        "health-management.html",
        students=students_optimized,
        today=today_str,
        selected_date=selected_date_str,
        progress_stats=progress_stats
    )


# ==================== MEAL MANAGEMENT ROUTES ====================
@app.route('/meal-management')
def meal_management():
    """
    Trang quản lý bữa ăn
    """
    # 1. Xử lý ngày tháng
    today_date = date.today()
    today_str = today_date.isoformat()
    date_str_from_request = request.args.get('date')

    selected_date = today_date
    if date_str_from_request:
        try:
            selected_date = datetime.strptime(date_str_from_request, '%Y-%m-%d').date()
        except ValueError:
            pass

    selected_date_str = selected_date.isoformat()
    current_month = selected_date.strftime('%Y-%m')

    # 2. Lấy danh sách học sinh từ database
    students = Student.query.filter(Student.active == True).all()

    # 3. Lấy cấu hình hệ thống để biết đơn giá bữa ăn
    meal_cost_per_day = dao.get_system_config('mealFee', default=50000)

    # 4. Tính tổng số ngày ăn trong tháng hiện tại dựa trên hóa đơn
    invoices = Invoice.query.filter(Invoice.active == True).all()

    monthly_meal_count = {s.id: 0 for s in students}
    for inv in invoices:
        if inv.createdAt and inv.createdAt.strftime('%Y-%m') == current_month:
            days = inv.mealDays or 0
            monthly_meal_count[inv.student_id] = monthly_meal_count.get(inv.student_id, 0) + days

    # 5. Chuẩn hóa dữ liệu cho template
    students_optimized = []
    for s in students:
        student_id = s.id

        # Hiện tại chưa có bảng chấm công bữa ăn theo ngày trong DB,
        # nên mặc định trạng thái "đã ăn hôm nay" là False
        daily_status = {
            today_str: {
                'ate_today': False
            }
        }

        students_optimized.append({
            'id': student_id,
            'name': f"{s.lastName} {s.firstName}",
            'daily_status': daily_status,
            'total_meals_eaten': monthly_meal_count.get(student_id, 0),
            'meal_cost': meal_cost_per_day
        })

    return render_template(
        "meal-management.html",
        students=students_optimized,
        today=today_str,
        selected_date=selected_date_str
    )


# ==================== TUITION MANAGEMENT ROUTES ====================
@app.route('/tuition')
def tuition():
    """
    Trang quản lý học phí
    """
    today_str = date.today().isoformat()

    # Lấy cấu hình hệ thống (học phí cơ bản, tiền ăn, sĩ số tối đa)
    base_tuition = dao.get_system_config('tuition', default=3000000)
    meal_cost_per_day = dao.get_system_config('mealFee', default=50000)

    # Lấy danh sách hóa đơn + join học sinh
    invoices = (
        db.session.query(Invoice)
        .join(Student, Student.id == Invoice.student_id)
        .filter(Invoice.active == True)
        .all()
    )

    tuition_optimized = []
    for inv in invoices:
        student = Student.query.get(inv.student_id)
        if not student:
            continue

        meals_eaten = inv.mealDays
        base_fee = inv.tuition or base_tuition
        meal_fee = inv.mealFee or meal_cost_per_day
        total_meal_cost = meals_eaten * meal_fee
        total_fee = inv.total or (base_fee + total_meal_cost)

        tuition_optimized.append({
            'student_id': student.id,
            'name': f"{student.lastName} {student.firstName}",
            'parent': student.parentName,
            'meals_eaten_days': meals_eaten,
            'meal_cost': meal_fee,
            'base_fee': base_fee,
            'total_meal_cost': total_meal_cost,
            'calculated_total_fee': total_fee,
            'paid_status': inv.paymentDate is not None
        })

    return render_template(
        "tuition.html",
        tuition_records=tuition_optimized,
        today=today_str,
        base_meal_cost=meal_cost_per_day,
        base_tuition=base_tuition
    )


# ==================== STATISTICS ROUTES ====================
@app.route('/statistics')
def statistics():
    """
    Trang thống kê
    """
    today_str = date.today().isoformat()

    # 1. Lấy thống kê dashboard và dữ liệu biểu đồ từ DAO
    dashboard_stats = dao.get_dashboard_stats(today_str)
    chart_data = dao.get_chart_data()

    return render_template(
        "statistics.html",
        stats=dashboard_stats,
        gender_chart_data=chart_data['gender_chart'],
        revenue_chart_data=chart_data['revenue_chart'],
        weight_chart_data=chart_data['weight_chart']
    )


# ==================== INVOICE ROUTES ====================
@app.route('/invoice/<int:student_id>')
def invoice(student_id):
    data = get_invoice_data(student_id)
    if not data:
        abort(404)

    return render_template(
        'invoice.html',
        student=data['student'],
        invoice=data['invoice']
    )



# ==================== ADMIN ROUTES ====================
@app.route('/admin/class_management')
def admin_class_management():
    """
    Trang quản lý lớp học (Admin)
    """
    classes_data = [
        {
            'id': 1,
            'name': 'Lớp Mẫu Giáo 1',
            'level': 'Mẫu giáo',
            'teacher_name': 'Nguyễn Thị Lan',
            'current_students': 20,
            'max_capacity': 25,
            'bg_color': '#DBEAFE'
        },
        {
            'id': 2,
            'name': 'Lớp Mẫu Giáo 2',
            'level': 'Mẫu giáo',
            'teacher_name': 'Trần Thị Mai',
            'current_students': 23,
            'max_capacity': 25,
            'bg_color': '#FCE7F3'
        },
        {
            'id': 3,
            'name': 'Lớp Nhà Trẻ 1',
            'level': 'Nhà trẻ',
            'teacher_name': 'Cô Lê Thị Hoa',
            'current_students': 15,
            'max_capacity': 20,
            'bg_color': '#DBEAFE'
        }
    ]

    total_students = sum(c['current_students'] for c in classes_data)
    total_capacity = sum(c['max_capacity'] for c in classes_data)

    return render_template(
        "admin/class-management.html",
        classes=classes_data,
        total_students=total_students,
        total_capacity=total_capacity,
    )


@app.route('/admin/class_management/<int:class_id>')
def admin_class_students(class_id):
    """
    Trang quản lý học sinh của một lớp cụ thể (Admin)
    """
    today_str = date.today().isoformat()

    # Lọc học sinh theo class_id
    students = [s for s in ultils.load_students() if s.get('class_id') == class_id]
    all_health_records = ultils.load_health_records()

    # Tìm bản ghi sức khỏe mới nhất
    current_records = {}
    for record in all_health_records:
        student_id = record['student_id']
        record_date = record['date']

        if student_id not in current_records or record_date > current_records[student_id]['date']:
            current_records[student_id] = record

    students_optimized = []
    for student in students:
        student_id = student['id']
        student['current_record'] = current_records.get(student_id, {})
        students_optimized.append(student)

    return render_template(
        "student.html",
        students=students_optimized,
        today=today_str
    )


@app.route('/admin/teacher_management')
def admin_teacher_management():
    """
    Trang quản lý giáo viên (Admin)
    """
    teachers = [
        {
            'id': 101,
            'name': 'Cô Nguyễn Thị Lan',
            'class_name': 'Lớp Mẫu Giáo 1',
            'email': 'lan.nguyen@school.edu.vn',
            'phone': '0912345678',
            'start_date': '1/9/2023',
            'salary': '8.000.000 đ'
        },
        {
            'id': 102,
            'name': 'Cô Trần Thị Mai',
            'class_name': 'Lớp Mẫu Giáo 2',
            'email': 'mai.tran@school.edu.vn',
            'phone': '0907654321',
            'start_date': '1/9/2023',
            'salary': '8.000.000 đ'
        },
        {
            'id': 103,
            'name': 'Cô Lê Thị Hoa',
            'class_name': 'Lớp Nhà Trẻ 1',
            'email': 'hoa.le@school.edu.vn',
            'phone': '0901234567',
            'start_date': '15/1/2024',
            'salary': '7.500.000 đ'
        }
    ]
    return render_template(
        "admin/teacher-management.html",
        teachers=teachers
    )


@app.route('/admin/regulation_management')
def admin_regulation_management():
    """
    Trang quản lý quy định (Admin)
    """
    return render_template("admin/regulation-management.html")


@app.route('/admin/statistics')
def admin_statistics():
    """
    Trang thống kê (Admin)
    """
    return render_template("admin/statistics.html")


# ==================== MAIN ENTRY POINT ====================
if __name__ == '__main__':
    from QuanLyHocSinh import admin
    app.run(debug=True)