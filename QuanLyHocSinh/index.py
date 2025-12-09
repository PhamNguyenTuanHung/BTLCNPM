# index.py - Main Application Routes
# File này khởi tạo Flask app và định nghĩa các route chính

from datetime import datetime, date
from flask import render_template, request, redirect, jsonify, session
from flask_login import login_user, logout_user, current_user, login_required

from QuanLyHocSinh import app, dao, login as login_manager
from QuanLyHocSinh.ultils import ultils
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

    # 2. Tải dữ liệu cơ bản
    students = ultils.load_students()
    all_health_records = ultils.load_health_records()

    # 3. Tìm bản ghi sức khỏe mới nhất cho mỗi học sinh
    current_records = {}
    for record in all_health_records:
        student_id = record['student_id']
        record_date = record['date']

        if student_id not in current_records or record_date > current_records[student_id]['date']:
            current_records[student_id] = record

    # 4. Tối ưu hóa dữ liệu học sinh
    students_optimized = []
    for student in students:
        student_id = student['id']
        student['current_record'] = current_records.get(student_id, {})
        students_optimized.append(student)

    # 5. Trả về template
    return render_template(
        "student.html",
        students=students_optimized,
        today=today_str
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

    # 2. Tải dữ liệu
    students = ultils.load_students()
    all_health_records = ultils.load_health_records()

    # 3. Lọc bản ghi sức khỏe cho ngày được chọn
    students_optimized = []
    recorded_count = 0

    records_for_selected_date = {
        r['student_id']: r
        for r in all_health_records
        if r['date'] == selected_date_str
    }

    for student in students:
        student_id = student['id']
        current_record = records_for_selected_date.get(student_id, {})
        student['current_record'] = current_record

        if current_record and current_record.get('weight') and current_record.get('temp'):
            recorded_count += 1

        students_optimized.append(student)

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

    # 2. Tải dữ liệu
    students = ultils.load_students()
    all_meal_attendance = ultils.load_meal_records()

    # 3. Tính tổng ngày ăn trong tháng
    monthly_meal_count = {student['id']: 0 for student in students}

    for record in all_meal_attendance:
        record_date = datetime.strptime(record['date'], '%Y-%m-%d').date()
        record_month = record_date.strftime('%Y-%m')
        student_id = record['student_id']

        if record_month == current_month and record.get('ate_today') is True:
            if student_id in monthly_meal_count:
                monthly_meal_count[student_id] += 1

    # 4. Tối ưu hóa dữ liệu
    students_optimized = []
    attendance_for_selected_date = {
        r['student_id']: r
        for r in all_meal_attendance
        if r['date'] == selected_date_str
    }

    for student in students:
        student_id = student['id']

        # Gán trạng thái chấm công cho ngày được chọn
        attendance_record = attendance_for_selected_date.get(student_id, {})
        student['daily_status'] = {
            selected_date_str: {
                'ate_today': attendance_record.get('ate_today', False)
            }
        }

        # Gán tổng số ngày ăn
        student['total_meals_eaten'] = monthly_meal_count.get(student_id, 0)
        students_optimized.append(student)

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

    students = ultils.load_students()
    financial_records = ultils.load_financial_records()

    student_lookup = {s['id']: s for s in students}

    # Cấu hình chi phí
    MEAL_COST_PER_DAY = 50000

    # Tối ưu hóa dữ liệu
    tuition_optimized = []

    for record in financial_records:
        student_id = record['student_id']
        student_info = student_lookup.get(student_id)

        if student_info:
            # Ghép nối thông tin
            record['name'] = student_info.get('name')
            record['parent'] = student_info.get('parent')
            record['meal_cost'] = MEAL_COST_PER_DAY

            # Tính toán chi phí
            meals_eaten = record.get('meals_eaten_days', 0)
            base_fee = record.get('base_fee', 3000000)

            total_meal_cost = meals_eaten * MEAL_COST_PER_DAY

            record['total_meal_cost'] = total_meal_cost
            record['calculated_total_fee'] = base_fee + total_meal_cost
            record['paid'] = record.get('paid_status', False)

            tuition_optimized.append(record)

    return render_template(
        "tuition.html",
        tuition_records=tuition_optimized,
        today=today_str,
        base_meal_cost=MEAL_COST_PER_DAY
    )


# ==================== STATISTICS ROUTES ====================
@app.route('/statistics')
def statistics():
    """
    Trang thống kê
    """
    today_str = date.today().isoformat()

    # 1. Tải dữ liệu
    students = ultils.load_students()
    all_health_records = ultils.load_health_records()
    financial_records = ultils.load_financial_records()

    # 2. Tính toán thống kê
    dashboard_stats = ultils.get_dashboard_stats(
        students,
        all_health_records,
        financial_records,
        today_str
    )

    # 3. Dữ liệu cho biểu đồ
    gender_chart_data = ultils.get_gender_chart_data(students)
    revenue_chart_data = ultils.get_revenue_chart_data(financial_records)
    weight_chart_data = ultils.get_average_weight_chart_data(all_health_records)

    return render_template(
        "statistics.html",
        stats=dashboard_stats,
        gender_chart_data=gender_chart_data,
        revenue_chart_data=revenue_chart_data,
        weight_chart_data=weight_chart_data
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