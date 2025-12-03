from datetime import datetime, date

from flask import Blueprint, render_template

from QuanLyHocSinh.ultils import ultils

# from mywebapp import utils, mail, oauth, socketio

main = Blueprint('main', __name__, template_folder='templates')
admin = Blueprint('admin', __name__, url_prefix='/admin', template_folder='templates/admin')

@main.route('/')
@main.route('/students')
def students_page():
    # 1. Khởi tạo ngày tháng
    today_str = date.today().isoformat()

    # 2. Tải dữ liệu cơ bản
    students = ultils.load_students()
    all_health_records = ultils.load_health_records()
    print(all_health_records)

    current_records = {}

    for record in all_health_records:
        student_id = record['student_id']
        record_date = record['date']

        if student_id not in current_records or record_date > current_records[student_id]['date']:
            current_records[student_id] = record

    students_optimized = []
    for student in students:
        student_id = student['id']

        # Gán bản ghi mới nhất (bao gồm cả các trường weight, temp, note)
        # Nếu không tìm thấy, gán dictionary rỗng
        student['current_record'] = current_records.get(student_id, {})

        students_optimized.append(student)

    # 5. Trả về template
    return render_template(
        "student.html",
        students=students_optimized,  # students đã có trường 'current_record'
        today=today_str
    )


@main.route("/students", methods=["POST"])
def add_student():
    students = ultils.load_students()
    new_student = request.json
    new_student['id'] = max(int(s['id']) for s in students) + 1 if students else 1
    students.append(new_student)
    ultils.save_students(students)
    return jsonify({"success": True, "student": new_student})


from flask import request, jsonify


@main.route("/students", methods=["PUT"])
def update_student():
    students = ultils.load_students()
    updated = request.get_json()
    for s in students:
        if s['id'] == int(updated['id']):
            s.update(updated)
            ultils.save_students(students)
            return jsonify({"success": True, "student": s})
    return jsonify({"success": False, "message": "Student not found"})


@main.route('/health-management')
def health_management():
    # 1. Xử lý ngày tháng
    today_date = date.today()
    today_str = today_date.isoformat()
    date_str_from_request = request.args.get('date')

    selected_date = today_date
    if date_str_from_request:
        try:
            # Chuyển đổi chuỗi ngày từ URL sang đối tượng date
            selected_date = datetime.strptime(date_str_from_request, '%Y-%m-%d').date()
        except ValueError:
            # Nếu ngày không hợp lệ, giữ nguyên selected_date = today_date
            pass

    selected_date_str = selected_date.isoformat()

    students = ultils.load_students()
    all_health_records = ultils.load_health_records()

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


@main.route('/meal-management')
def meal_management():
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
    print(all_meal_attendance)

    # 3. TÍNH TOÁN TỔNG NGÀY ĂN TRONG THÁNG (CORE LOGIC)
    # Khởi tạo dict để lưu tổng số ngày ăn cho từng trẻ trong tháng hiện tại
    monthly_meal_count = {student['id']: 0 for student in students}

    # Lặp qua tất cả bản ghi chấm công (lịch sử)
    for record in all_meal_attendance:
        record_date = datetime.strptime(record['date'], '%Y-%m-%d').date()
        record_month = record_date.strftime('%Y-%m')
        student_id = record['student_id']

        # Chỉ tính những bản ghi thuộc tháng hiện tại và trẻ đã ăn
        if record_month == current_month and record.get('ate_today') is True:
            if student_id in monthly_meal_count:
                monthly_meal_count[student_id] += 1

    # 4. Tối ưu hóa dữ liệu: Gán trạng thái chấm công hôm nay và tổng ngày ăn
    students_optimized = []

    # Lọc chấm công hôm nay (selected_date) để hiển thị checkbox
    attendance_for_selected_date = {
        r['student_id']: r
        for r in all_meal_attendance
        if r['date'] == selected_date_str
    }

    for student in students:
        student_id = student['id']

        # 4a. Gán trạng thái chấm công cho ngày được chọn (cho checkbox)
        attendance_record = attendance_for_selected_date.get(student_id, {})
        student['daily_status'] = {
            selected_date_str: {
                'ate_today': attendance_record.get('ate_today', False)
            }
        }

        # 4b. Gán TỔNG SỐ NGÀY ĂN đã tính toán
        student['total_meals_eaten'] = monthly_meal_count.get(student_id, 0)

        students_optimized.append(student)

    # 5. Trả về template
    return render_template(
        "meal-management.html",
        students=students_optimized,
        today=today_str,
        selected_date=selected_date_str
    )


from flask import render_template
from datetime import date


@main.route('/tuition')
def tuition():
    today_str = date.today().isoformat()

    students = ultils.load_students()  # Tải thông tin cơ bản
    financial_records = ultils.load_financial_records()  # Tải hồ sơ tài chính


    student_lookup = {
        s['id']: s for s in students
    }

    # 4. Cấu hình hằng số (Giả định chi phí cơ bản là 25,000 VND/ngày)
    MEAL_COST_PER_DAY = 50000

    # 5. Tối ưu hóa dữ liệu: Ghép nối và Tính toán Chi phí
    tuition_optimized = []

    for record in financial_records:
        student_id = record['student_id']
        student_info = student_lookup.get(student_id)

        if student_info:
            # --- 5a. Ghép nối thông tin cơ bản ---
            record['name'] = student_info.get('name')
            record['parent'] = student_info.get('parent')
            record['meal_cost'] = MEAL_COST_PER_DAY  # Gán chi phí cơ bản/ngày

            # --- 5b. Tính toán chi phí thực tế ---
            meals_eaten = record.get('meals_eaten_days', 0)
            base_fee = record.get('base_fee', 3000000)  # Học phí cơ bản

            total_meal_cost = meals_eaten * MEAL_COST_PER_DAY

            # Cập nhật/Thêm trường tính toán
            record['total_meal_cost'] = total_meal_cost
            record['calculated_total_fee'] = base_fee + total_meal_cost

            # Đảm bảo trường 'paid' có sẵn (chuyển từ paid_status sang paid)
            record['paid'] = record.get('paid_status', False)

            tuition_optimized.append(record)

    # 6. Trả về template (Sử dụng template tuition.html)
    return render_template(
        "tuition.html",
        tuition_records=tuition_optimized,
        today=today_str,
        base_meal_cost=MEAL_COST_PER_DAY  # Truyền chi phí bữa ăn cơ bản cho tiêu đề
    )


@main.route('/statistics')
def statistics():
    today_str = date.today().isoformat()

    # 1. Tải toàn bộ dữ liệu cần thiết
    students = ultils.load_students()
    all_health_records = ultils.load_health_records()
    financial_records = ultils.load_financial_records()

    # 2. Tính toán các chỉ số thống kê (Stats Cards)
    dashboard_stats = ultils.get_dashboard_stats(
        students,
        all_health_records,
        financial_records,
        today_str
    )

    # 3. Tính toán dữ liệu cho biểu đồ (Chart Data)
    gender_chart_data = ultils.get_gender_chart_data(students)
    revenue_chart_data = ultils.get_revenue_chart_data(financial_records)
    weight_chart_data = ultils.get_average_weight_chart_data(all_health_records)

    # 4. Trả về template
    return render_template(
        "statistics.html",
        stats=dashboard_stats,
        gender_chart_data=gender_chart_data,
        revenue_chart_data=revenue_chart_data,
        weight_chart_data=weight_chart_data
    )


@admin.route('/class_management/<int:id>')
def students_page(id):
    # 1. Khởi tạo ngày tháng
    today_str = date.today().isoformat()

    # 2. Tải dữ liệu cơ bản
    students = ultils.load_students()
    all_health_records = ultils.load_health_records()
    print(all_health_records)

    current_records = {}

    for record in all_health_records:
        student_id = record['student_id']
        record_date = record['date']

        if student_id not in current_records or record_date > current_records[student_id]['date']:
            current_records[student_id] = record

    students_optimized = []
    for student in students:
        student_id = student['id']

        # Gán bản ghi mới nhất (bao gồm cả các trường weight, temp, note)
        # Nếu không tìm thấy, gán dictionary rỗng
        student['current_record'] = current_records.get(student_id, {})

        students_optimized.append(student)

    # 5. Trả về template
    return render_template(
        "student.html",
        students=students_optimized,  # students đã có trường 'current_record'
        today=today_str
    )
@admin.route('/statistics')
def statistics():
    return render_template(
        "statistics.html",
    )

@admin.route('/')
@admin.route('/class_management')
def class_management():
    classes_data = [
        {
            'id': 1,
            'name': 'Lớp Mẫu Giáo 1',
            'level': 'Mẫu giáo',
            'teacher_name': 'Nguyễn Thị Lan',
            'current_students': 20,
            'max_capacity': 25,
            'bg_color': '#DBEAFE'  # Ví dụ về cách truyền màu
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
        "class-management.html",
        classes=classes_data,
        total_students=total_students,
        total_capacity=total_capacity,
    )

@admin.route('/teacher_management')
def teacher_management():
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
        "teacher-management.html",
        teachers=teachers
    )

@admin.route('/regulation_management')
def regulation_management():
    return render_template(
        "regulation-management.html",
    )
#
# @main.before_request
# def update_last_active():
#     if current_user.is_authenticated:
#         now = datetime.utcnow()
#         last_active = current_user.LanCuoiHoatDong  # Tên field tiếng Việt bạn dùng
#
#         if not getattr(g, 'last_active_updated', False) and (
#                 not last_active or now - last_active > timedelta(minutes=1)
#         ):
#             utils.update_last_active(current_user)
#             g.last_active_updated = True
#
#
# @main.route('/login', methods=['GET', 'POST'])
# def login():
#     next_page = request.args.get('next')
#     username = ""
#     if request.method == "POST":
#         username = request.form.get('username')
#         password = request.form.get('password')
#         next_page = request.form.get('next') or next_page
#         user, msg = utils.check_login(username, password)
#
#         if user:
#             login_user(user)
#             cart_session = utils.get_cart()
#             cart_db = utils.get_cart(current_user.MaNguoiDung)
#             merged_cart = utils.merge_cart_dicts(cart_session, cart_db)
#             utils.save_cart(user.MaNguoiDung, merged_cart)
#             session.pop('cart', None)
#             flash('Đăng nhập thành công!', 'success')
#             utils.log_activity(current_user.MaNguoiDung,
#                                action='login',
#                                message=f'Đăng nhập thành công với tên đăng nhập: {username}')
#             if not next_page or not next_page.startswith('/'):
#                 next_page = url_for('main.home')
#             return redirect(next_page)
#         else:
#             flash(msg, 'danger')
#
#     return render_template('login.html', next=next_page, username=username)
#
#
# @main.route('/login/google')
# def login_google():
#     next_page = request.args.get('next') or '/'
#     session['next_page'] = next_page
#     redirect_uri = url_for('main.authorize_google', _external=True)
#     print(redirect_uri)
#     return oauth.google.authorize_redirect(redirect_uri)
#
#
# @main.route('/auth/google/callback')
# def authorize_google():
#     try:
#         token = oauth.google.authorize_access_token()
#     except Exception as e:
#         print("OAuth Error:", e)
#         print("Lỗi xác thực Google: " + str(e), "danger")
#         return redirect(url_for('main.login'))
#     user_info = oauth.google.userinfo()
#     if not user_info:
#         flash('Không lấy được thông tin từ Google', 'danger')
#         return redirect(url_for('main.login'))
#
#     email = user_info.get('email')
#     name = user_info.get('name')
#     avatar = user_info.get('picture')
#
#     user = utils.get_user_by_email(email)
#     if not user:
#         user = utils.create_user_from_google(email=email, name=name, avatar=avatar)
#
#     # Login user
#     login_user(user)
#     cart_session = utils.get_cart()
#     cart_db = utils.get_cart(current_user.MaNguoiDung)
#     merged_cart = utils.merge_cart_dicts(cart_session, cart_db)
#     utils.save_cart(user.MaNguoiDung, merged_cart)
#     session.pop('cart', None)
#     utils.log_activity(
#         user.MaNguoiDung,
#         action='login',
#         message=f'User {email} đăng nhập bằng Google thành công'
#     )
#
#     next_page = session.pop('next_page', None) or url_for('main.home')
#     flash('Đăng nhập bằng Google thành công!', 'success')
#     return redirect(next_page)
#
#
# @main.route('/register', methods=['GET', 'POST'])
# def register():
#     error_field = None
#     avatar_path = "https://res.cloudinary.com/dmwhvc8tc/image/upload/v1753408922/user_avatar/avatar_default.png"
#     if request.method == 'POST':
#         fullname = request.form.get('fullname', '').strip()
#         email = request.form.get('email', '').strip()
#         username = request.form.get('username', '').strip()
#         password = request.form.get('password', '').strip()
#         confirm_password = request.form.get('confirm_password', '').strip()
#         sdt = request.form.get('SDT', '').strip()
#
#         if not fullname:
#             flash("Họ tên không được để trống", "error")
#             error_field = "fullname"
#         elif not username:
#             flash("Tên đăng nhập không được để trống", "error")
#             error_field = "username"
#         elif not email:
#             flash("Email không được để trống", "error")
#             error_field = "email"
#         elif password != confirm_password:
#             flash("Mật khẩu không khớp", "error")
#             error_field = "password"
#         elif not sdt:
#             flash("Số điện thoại không được để trống", "error")
#             error_field = "SDT"
#         elif utils.is_username_exist(username):
#             flash("Đã tồn tại tài khoản", "danger")
#             error_field = "username"
#         elif utils.is_email_exist(email):
#             flash("Email này đã được đăng ký", "danger")
#             error_field = "email"
#
#         if error_field:
#             return render_template(
#                 "user/register.html",
#                 fullname=fullname,
#                 username=username,
#                 email=email,
#                 SDT=sdt,
#                 error_field=error_field
#             )
#         else:
#             # 1. Tạo người dùng mới
#             user = utils.add_user(
#                 fullname=fullname,
#                 username=username,
#                 password=password,
#                 email=email,
#                 sdt=sdt,
#                 avatar=avatar_path
#             )
#
#             login_user(user)
#             utils.log_activity(user.MaNguoiDung, 'register', f'Đăng ký thành công với username: {username}')
#             return redirect('/')
#
#     return render_template('register.html')
#
#
# @main.route('/logout')
# @login_required
# def logout():
#     utils.log_activity(current_user.MaNguoiDung,
#                        action='logout',
#                        message=f'Đăng xuất thành công')
#     logout_user()  # Xoá session hiện tại (đăng xuất)
#     flash("Đăng xuất thành công!", "info")
#     return redirect('/')  # hoặc chuyển về trang chủ
#
#
# @main.route('/user/profile')
# def profile_details():
#     return render_template('profile_details.html')
#
#
# @main.route('/user/change-password')
# def change_password_view():
#     return render_template('change_password.html')
#
#
# @main.route('/api/user/profile', methods=['POST'])
# @login_required
# def api_update_user():
#     # Lưu giá trị cũ
#     old_name = current_user.HoTen
#     old_email = current_user.Email
#     old_phone = current_user.SoDienThoai
#     old_avatar = current_user.AnhDaiDien
#
#     # Lấy giá trị mới
#     name = request.form.get('name', '').strip()
#     email = request.form.get('email', '').strip()
#     phone = request.form.get('phone', '').strip()
#     avatar = request.files.get('avatar')
#
#     avatar_url = old_avatar  # mặc định giữ nguyên
#
#     # Nếu có file ảnh mới → upload lên Cloudinary
#     if avatar and avatar.filename != '' and avatar.mimetype.startswith('image/'):
#         try:
#             res = uploader.upload(
#                 avatar,
#                 folder="user_avatar",
#                 public_id=f"user_{current_user.MaNguoiDung}_avatar",
#                 overwrite=True
#             )
#             avatar_url = res['secure_url']
#         except Exception:
#             return {'success': False, 'error': 'Upload ảnh thất bại'}, 400
#
#     # Cập nhật user
#     result, updated_user = utils.update_user(
#         user_id=current_user.MaNguoiDung,
#         name=name,
#         email=email,
#         phone=phone,
#         avatar=avatar_url
#     )
#
#     if result:
#         # So sánh để tạo log chi tiết
#         changes = []
#         if old_name != name:
#             changes.append(f"Họ tên: '{old_name}' → '{name}'")
#         if old_email != email:
#             changes.append(f"Email: '{old_email}' → '{email}'")
#         if old_phone != phone:
#             changes.append(f"SĐT: '{old_phone}' → '{phone}'")
#         if old_avatar != avatar_url:
#             changes.append(f"Ảnh đại diện: đổi mới")
#
#         change_message = "; ".join(changes) if changes else "Không có thay đổi"
#
#         # Ghi log
#         utils.log_activity(
#             user_id=current_user.MaNguoiDung,
#             action='update_profile',
#             message=f"User {current_user.MaNguoiDung} cập nhật: {change_message}")
#
#         if updated_user:
#             return {
#                 'success': True,
#                 'name': updated_user.HoTen,
#                 'email': updated_user.Email,
#                 'phone': updated_user.SoDienThoai,
#                 'avatar': updated_user.AnhDaiDien
#             }
#     else:
#         return {'success': False, 'message': updated_user}, 500
#
#
# @main.route('/user/address')
# @login_required
# def view_address():
#     addresses = utils.get_user_addresses_by_id(user_id=current_user.MaNguoiDung)
#     return render_template('address.html', addresses=addresses)
#
#
# @main.route('/user/vouchers')
# @login_required
# def view_vouchers():
#     coupons = utils.get_user_vouchers(user_id=current_user.MaNguoiDung)
#     return render_template('voucher.html', coupons=coupons)
#
#
# @main.route('/user/dashboard')
# def dashboard():
#     orders = utils.get_recent_orders(current_user.MaNguoiDung, 3)
#     return render_template('dashboard.html', orders=orders)
#
#
# @main.route('/user/order')
# @login_required
# def order():
#     return render_template('order.html')
#
#
# @main.context_processor
# def inject_cart_count():
#     if current_user.is_authenticated:
#         cart = utils.get_cart(current_user.MaNguoiDung)
#     else:
#         cart = utils.get_cart()
#     cart_count = utils.count_cart(cart)
#     return dict(cart=cart, cart_count=cart_count)
#
#
# @main.route('/cart')
# def cart():
#     if current_user.is_authenticated:
#         cart = utils.get_cart(current_user.MaNguoiDung)
#     else:
#         cart = utils.get_cart()
#     cart_count = utils.count_cart(cart)
#     return render_template('cart.html', cart=cart, cartCount=cart_count)
#
#
# @main.route('/products/<int:product_id>')
# def product_detail(product_id):
#     product = utils.get_product_by_id(product_id)
#     related_products = utils.related_products(product_id=product_id)
#     reviews = utils.get_product_reviews(product_id)
#
#     variants_data = utils.get_sizes_and_colors_by_product_id(product_id)
#     sizes = variants_data.get('sizes', [])
#     colors = variants_data.get('colors', [])
#
#     gallery = utils.get_gallery(product_id)
#
#     return render_template(
#         'product_single.html',
#         product=product,
#         related_products=related_products,
#         sizes=sizes,
#         colors=colors,
#         reviews=reviews,
#         gallery=gallery
#     )
#
#
# @main.route('/checkout', methods=['GET'])
# @login_required
# def checkout():
#     addresses = utils.get_user_addresses_by_id(current_user.MaNguoiDung)
#     selected_keys = session.get('checkout_items', None)
#     if not selected_keys:
#         flash("Không có sản phẩm được chọn", "warning")
#         return redirect(url_for('main.cart'))
#
#     selected_items = []
#     for key in selected_keys:
#         item = utils.get_cart(current_user.MaNguoiDung, key=key)
#         if item:
#             selected_items.append(item)
#
#     cart_summary = utils.count_cart(selected_items)
#     vouchers = utils.get_user_vouchers(current_user.MaNguoiDung)
#
#     return render_template('checkout.html',
#                            cart_items=selected_items,
#                            cart_summary=cart_summary,
#                            addresses=addresses,
#                            vouchers=vouchers)
#
#
# @main.route('/')
# def home():
#     products = utils.load_products()
#     categories = utils.get_categories(quantity=3)
#     flash_sale = utils.get_active_sales()
#     return render_template('index.html', products=products, categories=categories, flash_sale=flash_sale)
#
#
# @main.route('/payment/return')
# def momo_return():
#     result_code = request.args.get("resultCode")
#     order_id = request.args.get("orderId")
#     message = request.args.get("message")
#     if result_code == "0":
#         return render_template('confirmation.html')
#     else:
#         return f"Thanh toán thất bại! Đơn hàng {order_id} - {message}"
#
#
# @main.route('/shop')
# def shop():
#     return render_template('shop.html')
#
#
# @main.route('/confirmation')
# def confirmation():
#     return render_template('confirmation.html')
#
#
# @main.route('/forget-password', methods=['GET', 'POST'])
# def forget_password():
#     if request.method == 'POST':
#         email = request.form.get('email')
#         print(email)
#         if not email:
#             flash('Vui lòng nhập email!', 'danger')
#             return redirect(url_for('main.forget_password'))
#
#         session['email'] = email
#         otp = utils.create_otp(email)
#
#         msg = Message(
#             subject="Lấy lại mật khẩu",
#             sender=current_app.config['MAIL_USERNAME'],
#             recipients=[email],
#             body=f"Mã OTP của bạn là: {otp}"
#         )
#         mail.send(msg)
#
#         flash('OTP đã được gửi vào email của bạn', 'success')
#         return redirect(url_for('main.verify_otp'))
#
#     return render_template('forget_password.html')
#
#
# @main.route('/verify-otp', methods=['GET', 'POST'])
# def verify_otp():
#     email = session.get('email')
#     if not email:
#         flash('Vui lòng nhập email trước', 'danger')
#         return redirect(url_for('forget_password'))
#     if request.method == 'POST':
#         otp_input = request.form.get('otp')
#         if utils.verify_otp(email, otp_input):
#             flash('OTP hợp lệ! Vui lòng đặt mật khẩu mới.', 'success')
#             return redirect(url_for('main.reset_password'))
#         else:
#             flash('OTP không đúng hoặc đã hết hạn', 'danger')
#     return render_template('verify_otp.html', email=email)
#
#
# @main.route('/reset-password', methods=['GET', 'POST'])
# def reset_password():
#     email = session.get('email')
#     if not email:
#         flash('Vui lòng nhập email trước', 'danger')
#         return redirect(url_for('main.forget_password'))
#     if request.method == 'POST':
#         new_password = request.form.get('password')
#         utils.update_password(email, new_password)
#         user = utils.get_user_by_email(email)
#         utils.delete_otp(email)
#         session.pop('email', None)
#
#         utils.log_activity(
#             user_id=user.MaNguoiDung,
#             action='Reset password',
#             message=f"{user.HoTen} đã đổi mật khẩu"
#         )
#
#         flash('Đổi mật khẩu thành công!', 'success')
#         return redirect(url_for('main.login'))
#     return render_template('reset_password.html', email=email)
#
#
# @main.route('/socket')
# def soket():
#     return render_template('soket.html')
#
#
# from flask_socketio import join_room, emit
#
#
# @socketio.on('join_room')
# @login_required
# def handle_join(data):
#     user_id = data['user_id'] if data else current_user.MaNguoiDung
#     conversation = utils.get_conversation(user_id=user_id, admin_id=1)
#     if conversation is None:
#         conversation = utils.create_conversation(current_user.MaNguoiDung, 1)
#     room = f"conversation_{conversation.MaCuocTroChuyen}"
#     join_room(room)
#
#     emit('joined_room', {
#         'conversation_id': conversation.MaCuocTroChuyen
#     })
#
#
# @socketio.on('load_conversation')
# def handle_load_conversation(data):
#     conversation_id = data['conversation_id']
#     messages = utils.get_messages(conversation_id)
#
#     emit('conversation_history',
#          {'messages': messages})
#
#
# @socketio.on('send_message')
# def handle_send_message(data):
#     message = data['message']
#     conversation_id = data['conversation_id']
#     sender_type = data['sender_type']
#     if sender_type == 'user':
#         utils.add_message(conversation_id,current_user.MaNguoiDung,message,sender_type)
#     else:
#         utils.add_message(conversation_id,1  , message,sender_type)
#     room = f"conversation_{conversation_id}"
#     emit('receive_message', {'message': message, 'sender_type': sender_type}, room=room)
