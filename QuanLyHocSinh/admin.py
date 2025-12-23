# admin.py - Flask-Admin Configuration
# Cấu hình giao diện quản trị cho dự án Quản lý học sinh

from flask import redirect
from flask_admin import Admin, AdminIndexView, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user, logout_user
from markupsafe import Markup
from sqlalchemy import or_
from wtforms.validators import ValidationError

from QuanLyHocSinh import dao
from QuanLyHocSinh import db, app
from QuanLyHocSinh.model import Student
from QuanLyHocSinh.model import User, Class, HealthRecord, Invoice, SystemConfig, UserRole, MealAttendance


# ==================== BASE ADMIN VIEW ====================
class AuthenticatedModelView(ModelView):
    """
    Base view yêu cầu xác thực và quyền ADMIN
    """
    
    # Enable export with both CSV and custom XLSX
    can_export = True
    export_types = ['csv', 'xlsx']
    
    def _export_xlsx(self):
        """
        Custom Excel export handler với formatting đẹp
        """
        from flask import Response
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.utils import get_column_letter
        from io import BytesIO
        from datetime import datetime
        
        # Get current view data
        count, query = self._get_list_filter_args()
        
        # Get columns to export  
        export_columns = self.get_export_columns()
        
        # Create workbook
        wb = Workbook()
        ws = wb.active
        ws.title = self.name or "Export"
        
        # Define styles
        # Header style
        header_font = Font(bold=True, color="FFFFFF", size=12)
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        header_border = Border(
            left=Side(style='thin', color="FFFFFF"),
            right=Side(style='thin', color="FFFFFF"),
            top=Side(style='thin', color="FFFFFF"),
            bottom=Side(style='thin', color="FFFFFF")
        )
        
        # Data cell border
        data_border = Border(
            left=Side(style='thin', color="D3D3D3"),
            right=Side(style='thin', color="D3D3D3"),
            top=Side(style='thin', color="D3D3D3"),
            bottom=Side(style='thin', color="D3D3D3")
        )
        
        # Alternating row colors
        even_fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
        odd_fill = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
        
        # Write headers
        for col_idx, col_name in enumerate(export_columns, 1):
            cell = ws.cell(row=1, column=col_idx, value=col_name)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
            cell.border = header_border
        
        # Write data with formatting
        for row_idx, row in enumerate(query.all(), 2):
            # Alternating row color
            row_fill = even_fill if row_idx % 2 == 0 else odd_fill
            
            for col_idx, col_name in enumerate(export_columns, 1):
                value = getattr(row, col_name, '')
                
                # Format value based on type
                if isinstance(value, datetime):
                    display_value = value.strftime('%d/%m/%Y %H:%M')
                elif value is None:
                    display_value = ''
                else:
                    display_value = str(value)
                
                cell = ws.cell(row=row_idx, column=col_idx, value=display_value)
                cell.border = data_border
                cell.fill = row_fill
                cell.alignment = Alignment(vertical="center")
        
        # Auto-size columns with limits
        for col_idx, column in enumerate(ws.columns, 1):
            max_length = 0
            column_letter = get_column_letter(col_idx)
            
            for cell in column:
                try:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                except:
                    pass
            
            # Set width with min and max limits
            adjusted_width = min(max(max_length + 2, 10), 50)
            ws.column_dimensions[column_letter].width = adjusted_width
        
        # Freeze header row
        ws.freeze_panes = 'A2'
        
        # Add auto-filter
        if len(export_columns) > 0:
            ws.auto_filter.ref = f"A1:{get_column_letter(len(export_columns))}1"
        
        # Set row height for header
        ws.row_dimensions[1].height = 30
        
        # Save to BytesIO
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        
        # Return response
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{self.name or 'export'}_{timestamp}.xlsx"
        
        return Response(
            output.getvalue(),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )

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


class ClassView(AuthenticatedModelView):
    column_list = [
        'id', 'name', 'numberStudent', 'max_capacity',
        'semester', 'fromYear', 'toYear', 'teacher'
    ]
    column_searchable_list = ['name']
    column_filters = ['semester', 'fromYear', 'toYear', 'teacher_id']
    column_editable_list = []
    page_size = 20
    form_excluded_columns = ['invoices']
    form_columns = [
        'name', 'semester', 'fromYear', 'toYear', 'active', 'teacher', 'students'
    ]

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
            # Tạo HealthRecord ban đầu cho học sinh mới
            from QuanLyHocSinh.model import HealthRecord
            from QuanLyHocSinh import db
            from datetime import datetime

            initial_health_record = HealthRecord(
                weight=0.0,
                bodyTemperature=36.5,
                note='',
                feverWarning=False,
                student_id=model.id,  # Lúc này model.id đã có giá trị
                recordingDate=datetime.utcnow()
            )
            db.session.add(initial_health_record)
            db.session.commit()


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
    column_list = ['id', 'student','student_id', 'mealDays', 'mealFee', 'tuition', 'total', 'paymentDate', 'teacher']
    column_searchable_list = []
    column_filters = ['paymentDate', 'createdAt', 'student_id', 'teacher_id','student.firstName']
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
        'teacher_id': 'ID Giáo viên',
        'student_name': 'Tên học sinh',
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


# ==================== MEAL ATTENDANCE VIEW ====================
class MealAttendanceView(AuthenticatedModelView):
    """
    Quản lý điểm danh bữa ăn
    """
    column_list = ['id', 'student', 'attendance_date', 'created_by_user', 'note', 'active']
    column_searchable_list = ['note']
    column_filters = ['attendance_date', 'student_id', 'created_by', 'active']
    column_labels = {
        'id': 'ID',
        'student': 'Học sinh',
        'student_id': 'Mã học sinh',
        'attendance_date': 'Ngày ăn',
        'created_by': 'Người tạo',
        'created_by_user': 'Giáo viên tạo',
        'note': 'Ghi chú',
        'active': 'Hoạt động'
    }
    can_export = True
    page_size = 50
    
    # Sắp xếp theo ngày mới nhất
    column_default_sort = ('attendance_date', True)
    
    # Custom formatter cho attendance_date
    def _attendance_date_formatter(view, context, model, name):
        from QuanLyHocSinh.utils import format_date_display
        if model.attendance_date:
            return model.attendance_date.strftime('%d/%m/%Y')
        return ''
    
    # Custom formatter to display created_by user info
    def _created_by_formatter(view, context, model, name):
        if model.created_by:
            user = User.query.get(model.created_by)
            if user:
                return f"{user.lastName} {user.firstName}"
        return ''
    
    column_formatters = {
        'attendance_date': _attendance_date_formatter,
        'created_by_user': _created_by_formatter
    }
    
    # Form configuration
    form_excluded_columns = []
    
    # Override to set default date to today
    def on_model_change(self, form, model, is_created):
        """
        Set created_by automatically if creating new record
        """
        if is_created and not model.created_by:
            model.created_by = current_user.id
        
        super(MealAttendanceView, self).on_model_change(form, model, is_created)


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


# ==================== STATISTICS VIEW ====================
class StatsView(BaseView):
    """
    Trang thống kê và báo cáo
    """

    @expose('/')
    def index(self):
        """
        Trang thống kê với biểu đồ tương tác (sidebar layout)
        """
        from sqlalchemy import func
        from QuanLyHocSinh import dao
        from datetime import date
        from flask import request
        
        # Get year from query parameter or use current year
        current_year = request.args.get('year', date.today().year, type=int)
        total_students = Student.query.filter_by(active=True).count()
        
        # 2. Tổng số lớp
        total_classes = Class.query.filter_by(active=True).count()
        
        # 3. Thống kê giới tính
        gender_stats = db.session.query(
            Student.gender,
            func.count(Student.id).label('count')
        ).filter(Student.active == True).group_by(Student.gender).all()
        
        male_count = sum(count for gender, count in gender_stats if gender)
        female_count = sum(count for gender, count in gender_stats if not gender)
        
        # 4. Thống kê sĩ số từng lớp
        class_enrollment = dao.get_class_enrollment_stats()
        
        # 5. Thống kê doanh thu theo năm được chọn
        monthly_revenue = dao.get_monthly_revenue_stats(year=current_year)
        
        stats_data = {
            'total_students': total_students,
            'total_classes': total_classes,
            'male_count': male_count,
            'female_count': female_count,
            'class_enrollment': class_enrollment,
            'monthly_revenue': monthly_revenue,
            'current_year': current_year
        }
        
        return self.render('admin/stats.html', **stats_data)
    
    @expose('/api/revenue-by-year')
    def get_revenue_by_year(self):
        """
        API endpoint để lấy dữ liệu doanh thu theo năm (AJAX)
        """
        from flask import request, jsonify
        from QuanLyHocSinh import dao
        from datetime import date
        
        year = request.args.get('year', date.today().year, type=int)
        revenue_data = dao.get_monthly_revenue_stats(year=year)
        
        return jsonify({
            'success': True,
            'data': revenue_data,
            'year': year
        })

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
admin.add_view(MealAttendanceView(MealAttendance, db.session, name='Điểm danh bữa ăn', category='Quản lý'))
admin.add_view(InvoiceView(Invoice, db.session, name='Hóa đơn'))
admin.add_view(SystemConfigView(SystemConfig, db.session, name='Cấu hình', category='Hệ thống'))
admin.add_view(StatsView(name='Thống kê & Báo cáo'))
admin.add_view(LogoutView(name='Đăng xuất'))
