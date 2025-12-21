from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import cloudinary

app = Flask(__name__)
app.secret_key = '&(^&*^&*^U*HJBJKHJLHKJHK&*%^&5786985646858'
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:Admin%40123@localhost/schooldb?charset=utf8mb4"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config["PAGE_SIZE"] = 8

# Session configuration for Flask-Login
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['REMEMBER_COOKIE_DURATION'] = 3600  # 1 hour

db = SQLAlchemy(app=app)
login = LoginManager(app=app)

# Cấu hình Flask-Login
login.login_view = 'login_view'  # Tên route để redirect khi chưa đăng nhập
login.login_message = 'Vui lòng đăng nhập để truy cập trang này.'
login.login_message_category = 'info'

cloudinary.config(cloud_name='dxxwcby8l',
api_key='792844686918347',
api_secret='T8ys_Z9zaKSqmKWa4K1RY6DXUJg')

# Context processor để inject thông tin lớp học vào template
@app.context_processor
def inject_teacher_class():
    """
    Inject thông tin lớp học mà giáo viên đang chủ nhiệm vào tất cả templates
    """
    from flask_login import current_user
    from QuanLyHocSinh import dao
    
    teacher_class = None
    class_name = "Trường Mầm Non Hoa Mai"  # Mặc định
    role_display = "Giáo viên"  # Mặc định
    
    if current_user.is_authenticated:
        # Hiển thị role
        role_display = "Quản trị viên" if current_user.user_role.name == 'ADMIN' else "Giáo viên"
        
        try:
            # Lấy học kỳ và năm học hiện tại từ SystemConfig
            current_semester = dao.get_system_config('HOC_KY', default=1)
            current_year = dao.get_system_config('NAM_HOC', default=2024)
            
            # Tìm lớp mà giáo viên đang chủ nhiệm
            from QuanLyHocSinh.model import Class
            teacher_class = Class.query.filter_by(
                teacher_id=current_user.id,
                semester=int(current_semester),
                fromYear=int(current_year),
                active=True
            ).first()
            
            if teacher_class:
                class_name = teacher_class.name
        except:
            pass
    
    return dict(
        teacher_class=teacher_class,
        current_class_name=class_name,
        current_user_fullname=f"{current_user.lastName} {current_user.firstName}" if current_user.is_authenticated else "",
        user_role_display=role_display
    )