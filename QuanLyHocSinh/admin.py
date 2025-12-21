# admin.py - Flask-Admin Configuration
# Cấu hình giao diện quản trị cho dự án Quản lý học sinh
import base64
import io
import matplotlib.pyplot as plt

import pdfkit
from flask import redirect, request, render_template, make_response
from flask_admin import Admin, AdminIndexView, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user, logout_user
from markupsafe import Markup
from sqlalchemy import or_
from wtforms.validators import ValidationError

from QuanLyHocSinh import dao
from QuanLyHocSinh import db, app
from QuanLyHocSinh.model import Student
from QuanLyHocSinh.model import User, Class, HealthRecord, Invoice, SystemConfig, UserRole


# ==================== BASE ADMIN VIEW ====================
class AuthenticatedModelView(ModelView):
    """
    Base view yêu cầu xác thực và quyền ADMIN
    """

    def is_accessible(self):
        print(
            f"[DEBUG] is_accessible called. is_authenticated: {current_user.is_authenticated}, user: {current_user}, role: {current_user.user_role if current_user.is_authenticated else 'N/A'}")
        return current_user.is_authenticated and current_user.user_role == UserRole.ADMIN

    def inaccessible_callback(self, name, **kwargs):
        print(f"[DEBUG] inaccessible_callback called for {name}")
        return redirect('/login')


# ==================== USER MANAGEMENT VIEW ====================
class UserView(AuthenticatedModelView):
    """
    Quản lý người dùng (Giáo viên, Admin)
    """
    column_list = ['id', 'firstName', 'lastName', 'username', 'email', 'phone', 'user_role', 'status']
    column_searchable_list = ['firstName', 'lastName', 'username', 'email']
    column_filters = ['user_role', 'status']
    column_editable_list = ['status', 'phone']
    column_labels = {
        'id': 'ID',
        'firstName': 'Tên',
        'lastName': 'Họ',
        'username': 'Tên đăng nhập',
        'email': 'Email',
        'phone': 'Số điện thoại',
        'user_role': 'Vai trò',
        'status': 'Trạng thái',
        'password': 'Mật khẩu'
    }
    can_export = True
    page_size = 20

    # Không cho phép xóa user
    can_delete = False

    # Ẩn password trong danh sách, nhưng HIỂN THỊ trong form
    column_exclude_list = ['password']
    form_excluded_columns = ['classes', 'invoices']

    # Override password field để dùng PasswordField
    from wtforms import PasswordField
    form_overrides = {
        'password': PasswordField
    }

    # Password không bắt buộc khi edit, chỉ bắt buộc khi create
    form_args = {
        'password': {
            'validators': []  # Bỏ required validator
        }
    }

    def on_model_change(self, form, model, is_created):
        """
        Được gọi trước khi lưu model.
        Hash password nếu có thay đổi.
        """
        import hashlib

        # Kiểm tra nếu form có trường password (không có khi inline edit)
        if hasattr(form, 'password') and form.password.data:
            # Hash password với MD5 (giống như logic hiện tại)
            model.password = str(hashlib.md5(form.password.data.encode('utf-8')).hexdigest())
        elif is_created:
            # Nếu tạo mới mà không có password, set default password
            default_password = '123456'
            model.password = str(hashlib.md5(default_password.encode('utf-8')).hexdigest())


# ==================== CLASS MANAGEMENT VIEW ====================


class ClassView(ModelView):
    column_list = [
        'id', 'name', 'numberStudent', 'max_capacity',
        'semester', 'fromYear', 'toYear', 'teacher'
    ]
    column_searchable_list = ['name']
    column_filters = ['semester', 'fromYear', 'toYear', 'teacher_id']
    column_editable_list = []
    can_export = True
    page_size = 20
    form_excluded_columns = ['invoices']
    form_columns = [
        'name', 'semester', 'fromYear', 'toYear', 'active', 'teacher', 'students'
    ]

    column_labels = {
        'id': 'ID',
        'name': 'Tên lớp',
        'numberStudent': 'Số học sinh hiện tại',
        'max_capacity': 'Sức chứa tối đa',
        'semester': 'Học kỳ',
        'fromYear': 'Năm bắt đầu',
        'toYear': 'Năm kết thúc',
        'teacher': 'Giáo viên phụ trách'
    }

    # ---------------- FORMATTERS ----------------
    def _current_student_count_formatter(view, context, model, name):
        return len(model.students) if model.students else 0

    def _max_capacity_formatter(view, context, model, name):
        max_cap = int(dao.get_system_config('maxNumber', default=40))
        current = len(model.students) if model.students else 0

        if current > max_cap:
            return Markup(f'<span style="color:red;font-weight:bold;">{current}/{max_cap} (Vượt quá!)</span>')
        elif current == max_cap:
            return Markup(f'<span style="color:orange;font-weight:bold;">{current}/{max_cap} (Đã đủ)</span>')
        else:
            return Markup(f'<span style="color:green;">{current}/{max_cap}</span>')

    column_formatters = {
        'numberStudent': _current_student_count_formatter,
        'max_capacity': _max_capacity_formatter
    }

    # ---------------- FORM ----------------
    def edit_form(self, obj=None):
        form = super().edit_form(obj)
        # Chỉ lấy HS chưa có lớp hoặc đang ở lớp này
        form.students.query = Student.query.filter(
            or_(Student.class_id == None, Student.class_id == obj.id)
        )
        return form

    def create_form(self):
        form = super().create_form()
        form.students.query = Student.query.filter(Student.class_id == None)
        return form

    # ---------------- VALIDATION ----------------
    def on_model_change(self, form, model, is_created):
        max_capacity = int(dao.get_system_config('maxNumber', default=40))
        new_count = len(form.students.data) if form.students.data else 0

        if new_count > max_capacity:
            raise ValidationError(
                f'Sĩ số lớp ({new_count}) vượt quá giới hạn ({max_capacity}). '
                'Vui lòng giảm số học sinh hoặc tăng giới hạn trong cấu hình.'
            )

        model.numberStudent = new_count


# ==================== STUDENT MANAGEMENT VIEW ====================
class StudentView(AuthenticatedModelView):
    """
    Quản lý học sinh
    """
    column_list = ['id', 'firstName', 'lastName', 'birthday', 'gender', 'parentName', 'parentPhone',
                   'guardianRelationship', 'class_']
    column_searchable_list = ['firstName', 'lastName', 'parentName', 'parentPhone']
    column_filters = ['gender', 'class_id', 'birthday']
    column_editable_list = ['parentPhone']
    column_labels = {
        'id': 'ID',
        'firstName': 'Tên',
        'lastName': 'Họ',
        'birthday': 'Ngày sinh',
        'gender': 'Giới tính',
        'parentName': 'Tên phụ huynh',
        'parentPhone': 'SĐT phụ huynh',
        'guardianRelationship': 'Quan hệ',
        'class_': 'Lớp',
        'class_id': 'ID Lớp'
    }
    can_export = True
    page_size = 30

    # Cấu hình form
    form_excluded_columns = ['health_records', 'invoices']

    # Cho phép class_id nullable (có thể thêm lớp sau)
    form_args = {
        'class_id': {
            'validators': []  # Bỏ required validator
        }
    }

    # Custom formatter cho cột giới tính
    def _gender_formatter(view, context, model, name):
        return 'Nam' if model.gender else 'Nữ'

    # Custom formatter cho cột ngày sinh - hiển thị dd/mm/yyyy
    def _birthday_formatter(view, context, model, name):
        from QuanLyHocSinh.utils import format_date_display
        return format_date_display(model.birthday)

    column_formatters = {
        'gender': _gender_formatter,
        'birthday': _birthday_formatter
    }

    # Override form fields
    from wtforms import RadioField, SelectField, StringField
    from wtforms.validators import DataRequired, Regexp

    form_overrides = {
        'gender': RadioField,
        'guardianRelationship': SelectField,
        'birthday': StringField  # Dùng StringField thay vì DateField để tự validate
    }

    # Cấu hình choices và format cho các field
    form_args = {
        'class_id': {
            'validators': []  # Bỏ required validator
        },
        'birthday': {
            'validators': [
                DataRequired('Ngày sinh là bắt buộc'),
                Regexp(r'^\d{2}/\d{2}/\d{4}$', message='Format phải là dd/mm/yyyy (vd: 03/10/2000)')
            ],
            'render_kw': {
                'placeholder': 'dd/mm/yyyy (vd: 03/10/2000)'
            }
        },
        'gender': {
            'choices': [(True, 'Nam'), (False, 'Nữ')],
            'coerce': lambda x: x == 'True' if isinstance(x, str) else bool(x)
        },
        'guardianRelationship': {
            'choices': [
                ('', '-- Chọn hoặc nhập tự do --'),
                ('Cha', 'Cha'),
                ('Mẹ', 'Mẹ'),
                ('Anh', 'Anh'),
                ('Chị', 'Chị'),
                ('Ông', 'Ông'),
                ('Bà', 'Bà'),
                ('Cô', 'Cô'),
                ('Dì', 'Dì'),
                ('Chú', 'Chú'),
                ('Bác', 'Bác')
            ],
            'validate_choice': False  # Cho phép nhập giá trị không có trong danh sách
        }
    }

    # Load custom CSS để hiển thị gender radio buttons theo hàng ngang
    extra_css = ['/static/admin/custom.css']

    def on_model_change(self, form, model, is_created):
        """
        Convert birthday string (dd/mm/yyyy) to datetime object before saving
        """
        from QuanLyHocSinh.utils import parse_date_input

        # Convert birthday từ string sang datetime
        if hasattr(form, 'birthday') and form.birthday.data:
            if isinstance(form.birthday.data, str):
                model.birthday = parse_date_input(form.birthday.data)

        super(StudentView, self).on_model_change(form, model, is_created)

    def after_model_change(self, form, model, is_created):
        """
        Tự động tạo bản ghi sức khỏe ban đầu khi tạo học sinh mới
        Method này được gọi SAU KHI student đã được commit, nên model.id đã có giá trị
        """
        super(StudentView, self).after_model_change(form, model, is_created)

        if is_created:
            from QuanLyHocSinh.model import HealthRecord, Invoice  # Import thêm Invoice
            from QuanLyHocSinh import db, dao  # Giả sử bạn có file dao để lấy config
            from datetime import datetime

            now = datetime.now()

            # 1. Tạo HealthRecord ban đầu
            initial_health_record = HealthRecord(
                weight=0.0,
                bodyTemperature=36.5,
                note='Khởi tạo hệ thống',
                feverWarning=False,
                student_id=model.id,
                recordingDate=now
            )
            db.session.add(initial_health_record)

            # 2. Tự động tạo Hóa đơn tháng hiện tại
            # Lấy tiền học và tiền ăn mặc định từ cấu hình hệ thống
            tuition_fee = 3000000  # Hoặc dao.get_system_config('tuition', 3000000)
            meal_fee_unit = 50000  # Hoặc dao.get_system_config('mealFee', 50000)

            initial_invoice = Invoice(
                student_id=model.id,
                teacher_id=model.class_.teacher_id if model.class_ else None,
                month=now.month,
                year=now.year,
                tuition=tuition_fee,
                mealDays=0,  # Mới thêm nên số ngày ăn bằng 0
                mealFee=meal_fee_unit,
                total=tuition_fee,  # Tổng tiền tạm tính bằng tiền học phí
                paymentDate=None  # Chưa thanh toán
            )
            db.session.add(initial_invoice)

            # Lưu tất cả thay đổi
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()


# ==================== HEALTH RECORD VIEW ====================
class HealthRecordView(AuthenticatedModelView):
    """
    Quản lý hồ sơ sức khỏe
    """
    column_list = ['id', 'student.id', 'student', 'weight', 'bodyTemperature', 'recordingDate', 'feverWarning', 'note']
    column_searchable_list = ['note']
    column_filters = ['recordingDate', 'feverWarning', 'student_id', 'student']
    column_labels = {
        'id': 'Mã bản ghi',
        'student.id': 'Mã học sinh',
        'student': 'Học sinh',
        'weight': 'Cân nặng (kg)',
        'bodyTemperature': 'Nhiệt độ (°C)',
        'recordingDate': 'Ngày ghi nhận',
        'feverWarning': 'Cảnh báo sốt',
        'note': 'Ghi chú',
    }
    can_export = True
    page_size = 25

    # Sắp xếp theo ngày mới nhất
    column_default_sort = ('recordingDate', True)

    # Custom formatter cho recordingDate
    def _recording_date_formatter(view, context, model, name):
        from QuanLyHocSinh.utils import format_datetime_display
        return format_datetime_display(model.recordingDate)

    column_formatters = {
        'recordingDate': _recording_date_formatter
    }


# ==================== INVOICE VIEW ====================
class InvoiceView(AuthenticatedModelView):
    """
    Quản lý hóa đơn học phí
    """
    column_list = ['id', 'student', 'mealDays', 'mealFee', 'tuition', 'total', 'paymentDate', 'teacher']
    column_searchable_list = []
    column_filters = ['paymentDate', 'createdAt', 'student_id', 'teacher_id']
    column_labels = {
        'id': 'ID',
        'student': 'Học sinh',
        'mealDays': 'Số ngày ăn',
        'mealFee': 'Phí ăn (VND)',
        'tuition': 'Học phí (VND)',
        'total': 'Tổng cộng (VND)',
        'paymentDate': 'Ngày thanh toán',
        'createdAt': 'Ngày tạo',
        'teacher': 'Giáo viên tạo',
        'student_id': 'ID Học sinh',
        'teacher_id': 'ID Giáo viên'
    }
    can_export = True
    page_size = 30

    # Custom formatters cho datetime fields
    def _payment_date_formatter(view, context, model, name):
        from QuanLyHocSinh.utils import format_datetime_display
        return format_datetime_display(model.paymentDate)

    def _created_at_formatter(view, context, model, name):
        from QuanLyHocSinh.utils import format_datetime_display
        return format_datetime_display(model.createdAt)

    column_formatters = {
        'paymentDate': _payment_date_formatter,
        'createdAt': _created_at_formatter
    }

    # Sắp xếp theo ngày tạo mới nhất
    column_default_sort = ('createdAt', True)


# ==================== SYSTEM CONFIG VIEW ====================
class SystemConfigView(AuthenticatedModelView):
    """
    Quản lý cấu hình hệ thống
    """
    column_list = ['id', 'key', 'value', 'note', 'createdAt', 'updatedAt']
    column_searchable_list = ['key', 'note']
    column_editable_list = ['value', 'note']
    column_labels = {
        'id': 'ID',
        'key': 'Từ khóa cấu hình',
        'value': 'Giá trị',
        'note': 'Ghi chú',
        'createdAt': 'Ngày tạo',
        'updatedAt': 'Ngày cập nhật'
    }
    can_export = True
    page_size = 20

    # Sắp xếp theo key
    column_default_sort = ('key', False)

    def on_model_change(self, form, model, is_created):
        """
        model: instance SystemConfig vừa được lưu
        is_created: True nếu là thêm mới, False nếu là sửa
        """
        from QuanLyHocSinh.model import Invoice, db

        # Chỉ update những hóa đơn chưa thanh toán
        today = datetime.today()
        current_month = today.month
        current_year = today.year

        # Chỉ lấy các hóa đơn chưa thanh toán của tháng hiện tại
        invoices = Invoice.query.filter(
            Invoice.paymentDate == None,
            Invoice.month == current_month,
            Invoice.year == current_year
        ).all()
        for inv in invoices:
            if model.key == 'mealFee':
                # Cập nhật mealFee từ config mới
                inv.mealFee = float(model.value)
                inv.total = (inv.tuition or 0) + (inv.mealFee or 0) * (inv.mealDays or 0)
            elif model.key == 'tuition':
                # Nếu bạn có key 'tuition' trong config để thay đổi học phí
                inv.tuition = float(model.value)
                inv.total = (inv.tuition or 0) + (inv.mealFee or 0) * (inv.mealDays or 0)
            # Có thể thêm các key khác tương tự

        db.session.commit()

        # Gọi super để giữ các xử lý mặc định của Flask-Admin
        return super().on_model_change(form, model, is_created)


# ==================== STATISTICS VIEW ====================

from collections import OrderedDict
from datetime import datetime


class StatsView(BaseView):
    @expose('/')
    def index(self):
        class_id = request.args.get('class_id', type=int)
        month = request.args.get('month', type=int)
        year = request.args.get('year', type=int)

        # ================== Tổng học sinh / lớp / giáo viên ==================
        students_query = Student.query
        if class_id:
            students_query = students_query.filter_by(class_id=class_id)
        total_students = students_query.count()
        total_classes = Class.query.count()
        total_teachers = User.query.filter_by(user_role=UserRole.TEACHER).count()

        # ================== Tỷ lệ nam/nữ ==================
        male_count = students_query.filter_by(gender=True).count()
        female_count = students_query.filter_by(gender=False).count()
        gender_ratio = {'male': male_count, 'female': female_count}

        # ================== Sĩ số theo lớp ==================
        class_sizes_raw = students_query.with_entities(
            Student.class_id, db.func.count(Student.id)
        ).group_by(Student.class_id).all()
        class_sizes = {}
        for cid, count in class_sizes_raw:
            class_name = "Chưa xếp lớp"
            if cid:
                c = Class.query.get(cid)
                class_name = c.name if c else "N/A"
            class_sizes[class_name] = count

        # ================== Doanh thu theo tháng ==================
        now = datetime.now()
        year_filter = year if year else now.year

        invoice_query = Invoice.query.join(Student)
        if class_id:
            invoice_query = invoice_query.filter(Student.class_id == class_id)
        if month:
            invoice_query = invoice_query.filter(Invoice.month == month)
        invoice_query = invoice_query.filter(Invoice.year == year_filter)

        revenue_by_month = OrderedDict((str(m), 0) for m in range(1, 13))
        total_revenue = sum(
            (inv.total if inv.total is not None else inv.calculated_total) or 0
            for inv in invoice_query.all()
        )
        for inv in invoice_query.all():
            # Sử dụng tổng thực tế nếu có, fallback sang calculated_total
            total_amount = inv.total if inv.total is not None else inv.calculated_total
            revenue_by_month[str(inv.month)] += total_amount or 0

        # ================== Danh sách lớp & năm cho filter ==================
        classes = Class.query.all()
        years = [y[0] for y in db.session.query(db.func.distinct(Invoice.year)).all()]

        return self.render('admin/statistics.html',
                           total_students=total_students,
                           total_classes=total_classes,
                           total_teachers=total_teachers,
                           total_revenue=total_revenue,
                           gender_ratio=gender_ratio,
                           class_sizes=class_sizes,
                           revenue_by_month=revenue_by_month,
                           classes=classes,
                           years=years)

    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role == UserRole.ADMIN

    def inaccessible_callback(self, name, **kwargs):
        return redirect('/login')


# ==================== LOGOUT VIEW ====================
class LogoutView(BaseView):
    """
    Đăng xuất khỏi admin panel
    """

    @expose('/')
    def index(self):
        logout_user()
        return redirect('/admin')

    def is_accessible(self):
        return current_user.is_authenticated


# ==================== CUSTOM ADMIN INDEX VIEW ====================
class MyAdminIndexView(AdminIndexView):
    """
    Trang chủ của admin panel
    """

    @expose('/')
    def index(self):
        # Thống kê tổng quan
        overview_stats = {
            'total_students': 0,
            'total_classes': 0,
            'total_teachers': 0,
            'total_revenue': 0
        }

        # Đếm từ database nếu có thể
        try:
            overview_stats['total_students'] = Student.query.count()
            overview_stats['total_classes'] = Class.query.count()
            overview_stats['total_teachers'] = User.query.filter_by(user_role=UserRole.TEACHER).count()
            overview_stats['total_revenue'] = db.session.query(db.func.sum(Invoice.total)).scalar() or 0
        except:
            pass

        return self.render('admin/index.html', stats=overview_stats)

    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role == UserRole.ADMIN

    def inaccessible_callback(self, name, **kwargs):
        return redirect('/login')


# ==================== FLASK-ADMIN INITIALIZATION ====================
admin = Admin(
    app=app,
    name='Quản lý Học sinh',
    index_view=MyAdminIndexView()
)

# Thêm các views vào admin panel
admin.add_view(ClassView(Class, db.session, name='Lớp học', category='Quản lý'))
admin.add_view(StudentView(Student, db.session, name='Học sinh', category='Quản lý'))
admin.add_view(UserView(User, db.session, name='Người dùng', category='Hệ thống'))
admin.add_view(HealthRecordView(HealthRecord, db.session, name='Hồ sơ sức khỏe', category='Quản lý'))
admin.add_view(InvoiceView(Invoice, db.session, name='Hóa đơn'))
admin.add_view(SystemConfigView(SystemConfig, db.session, name='Cấu hình', category='Hệ thống'))
admin.add_view(StatsView(name='Thống kê & Báo cáo'))
admin.add_view(LogoutView(name='Đăng xuất'))
