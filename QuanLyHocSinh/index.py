# index.py - Main Application Routes
# File này khởi tạo Flask app và định nghĩa các route chính

from flask import render_template, request, redirect, jsonify, abort
from flask_login import login_user, logout_user, current_user, login_required

from QuanLyHocSinh import app, login as login_manager, db
from QuanLyHocSinh import dao
from QuanLyHocSinh.ultils import ultils
import admin


# Import admin để khởi tạo Flask-Admin


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
    print(user)
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
    teacher_id = current_user.id
    page = request.args.get("page", 1, type=int)
    keyword = request.args.get("keyword", "").strip()

    class_id, current_student_count = dao.get_teacher_class_info(teacher_id)

    pagination = dao.load_students(
        class_id=class_id,
        page=page,
        page_size=9,
        kw=keyword
    )

    students = pagination.get('students')

    today_records = dao.get_today_health_records()

    students_view = dao.build_student_view(
        students,
        health_records=today_records,
        include_age=True,
        include_gender=True,
        include_parent=True,
        include_phone=True
    )

    max_capacity = int(
        dao.get_system_config('maxNumber', default=len(students_view))
    )

    return render_template(
        "student.html",
        students=students_view,
        pagination=pagination,
        current_student_count=current_student_count,
        max_capacity=max_capacity,
        today=date.today().isoformat()
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
    data = request.get_json()
    student_id = data.get('id')
    temp = data.get('temp')
    weight = data.get('weight')
    result = dao.save_health_record(student_id, record_date=None, temp=temp, weight=weight, note=None)

    if result:
        return jsonify({"success": True, "student": result})
    return jsonify({"success": False, "message": "Student not found"})


# ==================== HEALTH MANAGEMENT ROUTES ====================
@app.route('/health-management')
def health_management():
    today = date.today()
    today_str = today.isoformat()

    # Lấy ngày từ query param
    date_str = request.args.get('date')
    selected_date = today
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    selected_date_str = selected_date.isoformat()

    # Lấy các filter khác
    page = request.args.get('page', 1, type=int)
    keyword = request.args.get('keyword', '')
    updated_status = request.args.get('updated_status')
    fever = request.args.get('fever')


    teacher_id = current_user.id
    teacher_class_info = dao.get_teacher_class_info(teacher_id)

    # Load dữ liệu học sinh với filter trạng thái
    result = dao.load_students_with_health(
        teacher_id=teacher_id,
        date_filter=selected_date,
        page=page,
        kw=keyword,
        updated_status=updated_status,
        page_size=10,
        fever=fever
    )

    students_view = dao.build_student_view(
        result['students'],
        result['records_by_student']
    )

    progress_stats = dao.build_health_progress_stats(
        teacher_id=teacher_id,
        date=selected_date,
        total_students=teacher_class_info[1]
    )

    return render_template(
        "health-management.html",
        students=students_view,
        today=today_str,
        selected_date=selected_date_str,
        updated_status=updated_status,  # truyền vào template để đánh dấu dropdown
        keyword=keyword,
        progress_stats=progress_stats,
        pagination=result['pagination']
    )


@app.route('/health-management', methods=["POST"])
@login_required
def update_heath():
    data = request.get_json()
    temp = data['temp']
    weight = data['weight']
    note = data['note']
    student_id = data['id']
    record_date = date.today()
    record = dao.save_health_record(student_id, record_date, weight, temp, note)
    return jsonify({
        'success': True,
        "record": {
            "id": record.id,
            "student_id": record.student_id,
            "weight": record.weight,
            "temp": record.bodyTemperature,
            "note": record.note
        }
    })


# ==================== MEAL MANAGEMENT ROUTES ====================

@app.route('/meal-management')
@login_required
def meal_management():
    today = date.today()
    date_str = request.args.get('date')
    kw = request.args.get('keyword', '').strip()

    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else today
    except ValueError:
        selected_date = today

    # --- Tính toán dải ngày trong tuần ---
    start_of_week = selected_date - timedelta(days=selected_date.weekday())
    dates_in_week = [(start_of_week + timedelta(days=i)).isoformat() for i in range(7)]

    # Tính ngày cho nút Tuần trước / Tuần sau
    prev_week_date = (start_of_week - timedelta(days=7)).isoformat()
    next_week_date = (start_of_week + timedelta(days=7)).isoformat()

    # --- Lấy dữ liệu học sinh ---
    teacher_class = dao.get_class_by_teacher_id(current_user.id)
    class_id = teacher_class.id if teacher_class else None

    # Load toàn bộ học sinh trong lớp (hoặc theo search)
    pagination_data = dao.load_students(class_id=class_id, kw=kw, page_size=100)
    students = pagination_data['students']

    meal_cost_per_day = dao.get_system_config('mealFee', default=50000)

    students_data = []
    for s in students:
        weekly_attendance = dao.get_student_attendance_for_week(s.id, dates_in_week)
        total_meals_month = dao.count_meal_days(s.id, selected_date.month, selected_date.year)

        students_data.append({
            'id': s.id,
            'name': f"{s.lastName} {s.firstName}",
            'daily_status': weekly_attendance,
            'total_meals_eaten': total_meals_month,
            'meal_cost': meal_cost_per_day
        })

    return render_template(
        "meal-management.html",
        students=students_data,
        dates_in_week=dates_in_week,
        selected_date=selected_date.isoformat(),
        prev_week=prev_week_date,
        next_week=next_week_date,
        keyword=kw
    )


@app.route('/meal-attendance', methods=['POST'])
@login_required
def save_meal_attendance():
    # 1. Nhận data từ request
    data = request.json

    if not data or not isinstance(data, list):
        return jsonify({
            'success': False,
            'message': 'Dữ liệu không hợp lệ hoặc trống'
        }), 400

    # 2. Gọi logic xử lý từ DAO
    success, message = dao.update_meal_attendance(data, current_user.id)

    # 3. Trả về kết quả phù hợp cho Swal.fire nhận diện
    if success:
        return jsonify({'success': True, 'message': message})

    return jsonify({'success': False, 'message': message}), 500


# ==================== TUITION MANAGEMENT ROUTES ====================
@app.route('/tuition')
def tuition():
    today_str = date.today().isoformat()
    base_tuition = dao.get_system_config('tuition', default=3000000)
    meal_cost_per_day = dao.get_system_config('mealFee', default=50000)

    today = date.today()
    month = today.month
    year = today.year

    status = request.args.get('status')  # "paid" / "unpaid"
    keyword = request.args.get('keyword')  # search input

    invoices = dao.load_financial_records(month=month,
                                          year=year,
                                          status=status,
                                          keyword=keyword,
                                          teacher_id=current_user.id)

    return render_template(
        "tuition.html",
        invoices=invoices,
        today=today_str,
        base_meal_cost=meal_cost_per_day,
        base_tuition=base_tuition,
        selected_status=status,
        keyword=keyword
    )


# ==================== INVOICE ROUTES ====================
@app.route('/invoice/<int:invoice_id>')
def invoice(invoice_id):
    data = dao.get_invoice_data(invoice_id)
    if not data:
        abort(404)

    return render_template(
        'invoice.html',
        student=data['student'],
        invoice=data['invoice']
    )


from datetime import datetime, date, timedelta


@app.route('/api/invoices/pay', methods=['POST'])
def pay_tuition_fee():
    data = request.get_json()

    if not data or 'invoice_id' not in data:
        return jsonify({
            'success': False,
            'message': 'Thiếu invoice_id'
        }), 400

    invoice_id = data['invoice_id']

    dao.pay_invoice(invoice_id)

    return jsonify({
        'success': True,
    }), 200


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


# ==================== ADMIN ROUTES ====================
@app.route('/admin/class')
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


@app.route('/admin/class/<int:class_id>')
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


@app.route('/admin/teacher')
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
    app.run(debug=True)
