# admin.py - Flask-Admin Configuration
# Cấu hình giao diện quản trị cho dự án Quản lý học sinh

from flask_admin import Admin, AdminIndexView, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user, logout_user
from flask import redirect

from QuanLyHocSinh.model import User, Student, Class, HealthRecord, Invoice, SystemConfig, UserRole
from QuanLyHocSinh import db, app, dao


# ==================== BASE ADMIN VIEW ====================
class AuthenticatedModelView(ModelView):
    """
    Base view yêu cầu xác thực và quyền ADMIN
    """
    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role == UserRole.ADMIN

    def inaccessible_callback(self, name, **kwargs):
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
        
        # Nếu tạo mới hoặc password được cập nhật
        if form.password.data:
            # Hash password với MD5 (giống như logic hiện tại)
            model.password = str(hashlib.md5(form.password.data.encode('utf-8')).hexdigest())
        elif is_created:
            # Nếu tạo mới mà không có password, set default password
            default_password = '123456'
            model.password = str(hashlib.md5(default_password.encode('utf-8')).hexdigest())


# ==================== CLASS MANAGEMENT VIEW ====================
class ClassView(AuthenticatedModelView):
    """
    Quản lý lớp học
    """
    column_list = ['id', 'name', 'numberStudent', 'semester', 'fromYear', 'toYear', 'teacher']
    column_searchable_list = ['name']
    column_filters = ['semester', 'fromYear', 'toYear', 'teacher_id']
    column_editable_list = ['numberStudent']
    column_labels = {
        'id': 'ID',
        'name': 'Tên lớp',
        'numberStudent': 'Sĩ số',
        'semester': 'Học kỳ',
        'fromYear': 'Năm bắt đầu',
        'toYear': 'Năm kết thúc',
        'teacher': 'Giáo viên chủ nhiệm',
        'teacher_id': 'ID Giáo viên'
    }
    can_export = True
    page_size = 20


# ==================== STUDENT MANAGEMENT VIEW ====================
class StudentView(AuthenticatedModelView):
    """
    Quản lý học sinh
    """
    column_list = ['id', 'firstName', 'lastName', 'birthday', 'gender', 'parentName', 'parentPhone', 'class_']
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


# ==================== HEALTH RECORD VIEW ====================
class HealthRecordView(AuthenticatedModelView):
    """
    Quản lý hồ sơ sức khỏe
    """
    column_list = ['id', 'student', 'weight', 'bodyTemperature', 'recordingDate', 'feverWarning', 'note']
    column_searchable_list = ['note']
    column_filters = ['recordingDate', 'feverWarning', 'student_id']
    column_labels = {
        'id': 'ID',
        'student': 'Học sinh',
        'weight': 'Cân nặng (kg)',
        'bodyTemperature': 'Nhiệt độ (°C)',
        'recordingDate': 'Ngày ghi nhận',
        'feverWarning': 'Cảnh báo sốt',
        'note': 'Ghi chú',
        'student_id': 'ID Học sinh'
    }
    can_export = True
    page_size = 50
    
    # Sắp xếp theo ngày mới nhất
    column_default_sort = ('recordingDate', True)


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
    
    # Sắp xếp theo ngày tạo mới nhất
    column_default_sort = ('createdAt', True)


# ==================== SYSTEM CONFIG VIEW ====================
class SystemConfigView(AuthenticatedModelView):
    """
    Quản lý cấu hình hệ thống
    """
    column_list = ['id', 'tuition', 'maxNumber', 'mealFee', 'effectiveDate', 'createdAt', 'updatedAt']
    column_labels = {
        'id': 'ID',
        'tuition': 'Học phí (VND)',
        'maxNumber': 'Sĩ số tối đa',
        'mealFee': 'Phí ăn/ngày (VND)',
        'effectiveDate': 'Ngày hiệu lực',
        'createdAt': 'Ngày tạo',
        'updatedAt': 'Ngày cập nhật'
    }
    can_export = True
    page_size = 20
    
    # Sắp xếp theo ngày hiệu lực
    column_default_sort = ('effectiveDate', True)


# ==================== STATISTICS VIEW ====================
class StatsView(BaseView):
    """
    Trang thống kê và báo cáo
    """
    @expose('/')
    def index(self):
        # Lấy dữ liệu thống kê từ dao
        stats_data = {
            'total_students': len(dao.load_students()) if hasattr(dao, 'load_students') else 0,
            'total_classes': 0,  # Sẽ implement sau
            'revenue_stats': {}  # Sẽ implement sau
        }
        
        return self.render('admin/stats.html', **stats_data)

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
admin.add_view(InvoiceView(Invoice, db.session, name='Hóa đơn', category='Tài chính'))
admin.add_view(SystemConfigView(SystemConfig, db.session, name='Cấu hình', category='Hệ thống'))
admin.add_view(StatsView(name='Thống kê & Báo cáo'))
admin.add_view(LogoutView(name='Đăng xuất'))