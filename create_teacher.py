"""
Script để tạo teacher mới
Chạy: python create_teacher.py
"""
from QuanLyHocSinh import app, db
from QuanLyHocSinh.model import User, UserRole
import hashlib

with app.app_context():
    teacher = User(
        firstName='Huy',
        lastName='Do',
        username='teacher1',
        password=hashlib.md5('123456'.encode('utf-8')).hexdigest(),
        email='teacher1@school.edu.vn',
        phone='0909123456',
        user_role=UserRole.TEACHER
    )

    db.session.add(teacher)
    db.session.commit()

    print("✅ Đã tạo tài khoản TEACHER thành công")
