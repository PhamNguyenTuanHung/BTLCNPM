# index.py - Main Application Routes
# File này khởi tạo Flask app và định nghĩa các route chính

# Standard library
import hashlib
import calendar
import os
import logging
from datetime import date, datetime
from io import BytesIO

# Third-party
from flask import render_template, request, redirect, jsonify, abort, send_file
from flask_login import login_user, logout_user, current_user, login_required

# Application
from QuanLyHocSinh import app, dao, login as login_manager, db, admin
from QuanLyHocSinh.model import Student, HealthRecord, Invoice

# PDF support (optional)
try:
    from xhtml2pdf import pisa
    HAS_PDF_SUPPORT = True
except ImportError:
    HAS_PDF_SUPPORT = False


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
@login_required
def index():
    """
    Trang Dashboard/Homepage sau khi đăng nhập
    """
    teacher_id = current_user.id
    teacher_name = f"{current_user.lastName} {current_user.firstName}"
    
    # Lấy thông tin lớp học
    from QuanLyHocSinh.model import Class
    teacher_class = Class.query.filter_by(teacher_id=teacher_id, active=True).first()
    class_name = teacher_class.name if teacher_class else "Hoa Mai"
    
    _, current_student_count = dao.get_teacher_class_info(teacher_id)
    
    return render_template(
        "index.html",
        teacher_name=teacher_name,
        class_name=class_name,
        current_student_count=current_student_count
    )


@app.route('/students')
@login_required
def students():
    """
    Trang quản lý học sinh
    """
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

    # Lấy bản ghi sức khỏe MỚI NHẤT của các học sinh
    # (thay vì chỉ lấy hôm nay để luôn hiển thị dữ liệu)
    latest_records = dao.get_latest_health_records()

    students_view = dao.build_student_view(
        students,
        health_records=latest_records,
        include_age=True,
        include_gender=True,
        include_parent=True,
        include_phone=True
    )

    max_capacity = int(
        dao.get_system_config('SI_SO', default=len(students_view))
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
    result = dao.save_health_record(student_id,record_date=None, temp=temp, weight=weight,note=None)

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
    updated_status = request.args.get('updated_status')  # "updated" / "not_updated" / None

    teacher_id = current_user.id
    teacher_class_info = dao.get_teacher_class_info(teacher_id)

    # Load dữ liệu học sinh với filter trạng thái
    result = dao.load_students_with_health(
        teacher_id=teacher_id,
        date_filter=selected_date,
        page=page,
        kw=keyword,
        updated_status=updated_status,  # thêm filter
        page_size=10
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
        updated_status=updated_status,   # truyền vào template để đánh dấu dropdown
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
    record =dao.save_health_record(student_id, record_date, weight, temp, note)
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
    """
    Trang quản lý bữa ăn theo tuần
    """
    # 1. Get current week or week from query param
    week_offset = request.args.get('week', 0, type=int)  # 0 = current week, -1 = last week, +1 = next week
    
    # 2. Calculate week start/end dates
    week_dates = dao.get_week_dates(week_offset)
    
    # 3. Load students from teacher's class
    teacher_id = current_user.id
    teacher_class = dao.get_class_by_teacher_id(teacher_id)
    class_id = teacher_class.id if teacher_class else None
    
    students = dao.load_students(
        class_id=class_id,
        page_size=100  # Load all students
    ).get('students', [])
    
    # 4. Load meal attendance for the week
    student_ids = [s.id for s in students]
    meal_data = dao.get_weekly_meal_attendance(
        student_ids=student_ids,
        week_dates=week_dates
    )
    
    # 5. Prepare view data
    students_data = []
    today = date.today()
    meal_cost_per_day = dao.get_system_config('TIEN_AN_MOT_NGAY', default=30000)
    
    for s in students:
        # Calculate monthly total
        total_meals_month = dao.count_meal_days(
            student_id=s.id,
            month=today.month,
            year=today.year
        )
        
        # Get list of meal dates
        meal_dates = dao.get_meal_dates(
            student_id=s.id,
            month=today.month,
            year=today.year
        )
        
        students_data.append({
            'id': s.id,
            'name': f"{s.lastName} {s.firstName}",
            'weekly_attendance': meal_data.get(s.id, {}),  # {date: True/False}
            'total_meals_month': total_meals_month,
            'meal_dates': meal_dates,  # List of date objects
            'meal_cost': meal_cost_per_day
        })
    
    return render_template(
        "meal-management.html",
        students=students_data,
        week_dates=week_dates,
        week_offset=week_offset,
        meal_cost=meal_cost_per_day,
        current_month=today.month,
        current_year=today.year
    )




@app.route('/meal-attendance', methods=['POST'])
@login_required
def save_meal_attendance():
    """
    Lưu dữ liệu chấm công ăn uống (hỗ trợ cả single day và weekly)
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'message': 'Không có dữ liệu'}), 400
    
    try:
        dao.save_weekly_meal_attendance(
            attendance_data=data,
            teacher_id=current_user.id
        )
        return jsonify({'success': True, 'message': 'Đã lưu điểm danh thành công!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/meal-attendance/export-excel')
@login_required
def export_meal_attendance():
    """
    Xuất bảng điểm danh bữa ăn ra file Excel
    """
    # Get parameters
    month = request.args.get('month', date.today().month, type=int)
    year = request.args.get('year', date.today().year, type=int)
    
    # Get teacher's class
    teacher_id = current_user.id
    teacher_class = dao.get_class_by_teacher_id(teacher_id)
    
    if not teacher_class:
        return jsonify({'success': False, 'message': 'Không tìm thấy lớp học'}), 404
    
    # Get all students in class
    students = dao.load_students(
        class_id=teacher_class.id,
        page_size=100
    ).get('students', [])
    
    student_ids = [s.id for s in students]
    
    if not student_ids:
        return jsonify({'success': False, 'message': 'Không có học sinh'}), 404
    
    try:
        # Generate Excel in memory (BytesIO)
        excel_buffer = dao.export_meal_attendance_excel(
            student_ids=student_ids,
            month=month,
            year=year,
            class_name=teacher_class.name
        )
        
        # Return file for download from memory
        return send_file(
            excel_buffer,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'diem_danh_an_{month}_{year}.xlsx'
        )
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500




# ==================== TUITION MANAGEMENT ROUTES ====================
@app.route('/tuition')
@login_required
def tuition():
    """
    Trang quản lý học phí - chỉ hiển thị học sinh trong lớp của giáo viên
    """
    teacher_id = current_user.id
    today_str = date.today().isoformat()
    base_tuition = dao.get_system_config('HOC_PHI_CO_BAN', default=3000000)
    meal_cost_per_day = dao.get_system_config('TIEN_AN_MOT_NGAY', default=50000)

    today = date.today()
    month = today.month
    year = today.year

    # Lấy class của giáo viên
    class_id, _ = dao.get_teacher_class_info(teacher_id)
    
    if not class_id:
        # Nếu giáo viên không có lớp, hiển thị trang trống
        return render_template(
            "tuition.html",
            invoices=[],
            today=today_str,
            base_meal_cost=meal_cost_per_day,
            base_tuition=base_tuition,
            selected_status=None,
            keyword=None
        )

    status = request.args.get('status')       # "paid" / "unpaid"
    keyword = request.args.get('keyword')     # search input

    # Lấy danh sách invoice, filter theo class
    invoices = dao.load_financial_records(
        month=month, 
        year=year, 
        status=status, 
        keyword=keyword,
        class_id=class_id  # Thêm filter theo class
    )

    return render_template(
        "tuition.html",
        invoices=invoices,
        today=today_str,
        base_meal_cost=meal_cost_per_day,
        base_tuition=base_tuition,
        selected_status=status,
        keyword=keyword
    )


@app.route('/api/tuition/export-excel')
@login_required
def export_tuition_report():
    """
    Xuất báo cáo chi phí học phí ra file Excel
    """
    # Get parameters
    month = request.args.get('month', date.today().month, type=int)
    year = request.args.get('year', date.today().year, type=int)
    
    # Get teacher's class
    teacher_id = current_user.id
    class_id, _ = dao.get_teacher_class_info(teacher_id)
    
    if not class_id:
        return jsonify({'success': False, 'message': 'Không tìm thấy lớp học'}), 404
    
    # Get financial records
    invoices = dao.load_financial_records(
        month=month,
        year=year,
        class_id=class_id
    )
    
    if not invoices:
        return jsonify({'success': False, 'message': 'Không có dữ liệu'}), 404
    
    try:
        # Get class name
        teacher_class = dao.get_class_by_teacher_id(teacher_id)
        class_name = teacher_class.name if teacher_class else ""
        
        # Generate Excel in memory (BytesIO)
        excel_buffer = dao.export_tuition_report_excel(
            financial_records=invoices,
            month=month,
            year=year,
            class_name=class_name
        )
        
        # Return file for download from memory
        return send_file(
            excel_buffer,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'bao_cao_chi_phi_{month}_{year}.xlsx'
        )
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


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

from datetime import datetime, date


@app.route('/api/invoices/pay', methods=['POST'])
@login_required
def pay_tuition_fee():
    """
    Thanh toán học phí - tạo invoice nếu chưa có
    """
    data = request.get_json()

    if not data or 'invoice_id' not in data:
        return jsonify({
            'success': False,
            'message': 'Thiếu invoice_id'
        }), 400

    invoice_id = data['invoice_id']
    
    # Nếu invoice_id là None, cần tạo mới
    if invoice_id is None:
        # Lấy student_id từ request (frontend cần gửi thêm)
        student_id = data.get('student_id')
        if not student_id:
            return jsonify({
                'success': False,
                'message': 'Thiếu student_id'
            }), 400
        
        # Tạo invoice mới
        today = date.today()
        month = today.month
        year = today.year
        
        # Lấy config
        base_tuition = dao.get_system_config('HOC_PHI_CO_BAN', default=1500000)
        meal_cost_per_day = dao.get_system_config('TIEN_AN_MOT_NGAY', default=30000)
        
        # Tính số bữa ăn
        meal_days = dao.count_meal_days(student_id, month, year)
        total_meal_cost = meal_days * meal_cost_per_day
        total_amount = base_tuition + total_meal_cost
        
        # Tạo invoice
        new_invoice = Invoice(
            student_id=student_id,
            teacher_id=current_user.id,
            month=month,
            year=year,
            tuition=base_tuition,
            mealDays=meal_days,
            mealFee=meal_cost_per_day,
            total=total_amount,
            paymentDate=datetime.now(),
            active=True
        )
        
        db.session.add(new_invoice)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'invoice_id': new_invoice.id,
            'message': 'Thanh toán thành công'
        }), 200
    
    # Nếu đã có invoice, gọi hàm cũ
    result = dao.pay_invoice(invoice_id)
    
    if isinstance(result, tuple):
        response, status_code = result
        return jsonify(response), status_code
    
    return jsonify({
        'success': True,
    }), 200


@app.route('/api/invoices/export-pdf/<int:invoice_id>')
@login_required
def export_invoice_pdf(invoice_id):
    """
    Xuất hóa đơn ra file PDF
    - Xóa meal_attendance của tháng sau khi xuất (giữ mealDays trong invoice)
    """
    import os
    import unicodedata
    from QuanLyHocSinh.model import MealAttendance
    
    def remove_accents(text):
        """Remove Vietnamese accents from text"""
        if not text:
            return text
        # Normalize to NFD (decomposed form)
        nfd = unicodedata.normalize('NFD', str(text))
        # Filter out diacritical marks
        return ''.join(char for char in nfd if unicodedata.category(char) != 'Mn')
    
    # Check if PDF support is available
    if not HAS_PDF_SUPPORT:
        abort(500, description="PDF export not available. Please install xhtml2pdf: pip install xhtml2pdf")
    
    # Lấy dữ liệu invoice
    data = dao.get_invoice_data(invoice_id)
    if not data:
        abort(404, description="Invoice not found")
    
    # Remove accents from all text data
    student = data['student']
    invoice = data['invoice']
    
    # Create cleaned data for PDF
    pdf_data = {
        'student': {
            'firstName': remove_accents(student.firstName),
            'lastName': remove_accents(student.lastName),
            'parentName': remove_accents(student.parentName),
            'parentPhone': student.parentPhone,
            'class_': {
                'name': remove_accents(student.class_.name)
            } if student.class_ else {'name': 'Chua xep lop'}
        },
        'invoice': invoice
    }
    
    # Render HTML template - use PDF-specific template
    html_content = render_template('invoice_pdf.html', **pdf_data)
    
    # Suppress CSS parser warnings
    logging.getLogger('xhtml2pdf').setLevel(logging.ERROR)
    
    pdf_buffer = BytesIO()
    
    # Generate PDF in memory
    try:
        pisa_status = pisa.CreatePDF(
            src=html_content,
            dest=pdf_buffer,
            encoding='utf-8'
        )
    except Exception as e:
        print(f"PDF Generation Error: {e}")
        abort(500, description=f"Error generating PDF: {e}")
    
    if pisa_status.err:
        abort(500, description="Error generating PDF")
    
    # Seek to beginning of buffer
    pdf_buffer.seek(0)
    
    # XÓA meal_attendance của tháng này sau khi xuất PDF
    # (số ngày ăn đã được lưu trong invoice.mealDays)
    try:
        MealAttendance.query.filter(
            MealAttendance.student_id == student.id,
            db.func.extract('month', MealAttendance.date) == month,
            db.func.extract('year', MealAttendance.date) == year
        ).delete(synchronize_session=False)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Warning: Could not delete meal_attendance: {e}")
    
    # Return PDF from memory (not from file)
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=False,
        download_name=f'invoice_{invoice_id}.pdf'
    )

# ==================== MAIN ENTRY POINT ====================
if __name__ == '__main__':
    app.run(debug=True)
