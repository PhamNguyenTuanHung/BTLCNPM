from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

# Giả sử đối tượng db (SQLAlchemy) đã được định nghĩa và khởi tạo trong create_app()

db = SQLAlchemy()


class User(UserMixin, db.Model):
    # Tên bảng trong cơ sở dữ liệu
    __tablename__ = 'Users'

    # Cần phải có primary key 'id' để Flask-Login hoạt động
    id = db.Column(db.Integer, primary_key=True)

    # Các trường thông tin khác
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    role = db.Column(db.String(50), default='teacher')  # Ví dụ: 'admin', 'teacher', 'parent'

    # Phương thức để in ra đối tượng (hữu ích cho debugging)
    def __repr__(self):
        return f'<User {self.username}>'

    # Phương thức get_id() được cung cấp bởi UserMixin, Flask-Login sẽ gọi nó.

# Lưu ý: Khi sử dụng Flask-SQLAlchemy, đối tượng 'db' cần được truyền vào
# hoặc được khởi tạo như một đối tượng toàn cục trong cấu trúc ứng dụng của bạn.