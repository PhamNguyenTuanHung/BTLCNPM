# model.py
from sqlalchemy import (
    Column, Integer, String, Boolean, Float, Numeric, DateTime, ForeignKey, Enum, Date, Index
)
from sqlalchemy.orm import relationship
from flask_login import UserMixin
from datetime import datetime

from enum import Enum as UserEnum
from QuanLyHocSinh import db, app


class BaseModel(db.Model):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)
    active = Column(Boolean, default=True)

# ========== ENUM ROLE THAY CHO BẢNG ROLE ==========
class UserRole(UserEnum):
    TEACHER = 1
    ADMIN = 2


# ======================= USER =======================
class User(BaseModel, UserMixin):
    __tablename__ = 'users'

    firstName = Column(String(100), nullable=False)
    lastName = Column(String(100), nullable=False)
    username = Column(String(100), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    phone = Column(String(20))
    status = Column(Boolean, default=True)

    # ROLE là ENUM — KHÔNG tạo bảng Role
    user_role = Column(Enum(UserRole), default=UserRole.TEACHER)

    # Quan hệ 1-n với Class
    classes = relationship(
        'Class',
        backref='teacher',
        lazy=True,
        foreign_keys='Class.teacher_id'
    )

    # Quan hệ 1-n với Invoice
    invoices = relationship(
        'Invoice',
        backref='teacher',
        lazy=True,
        foreign_keys='Invoice.teacher_id'
    )

    def __str__(self):
        return f"{self.lastName} {self.firstName}"


# ======================== CLASS ========================
class Class(BaseModel):
    __tablename__ = 'classes'

    name = Column(String(100), nullable=False)
    numberStudent = Column(Integer, nullable=False)
    semester = Column(Integer, nullable=False)
    fromYear = Column(Integer, nullable=False)
    toYear = Column(Integer, nullable=False)

    teacher_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    students = relationship('Student', backref='class_', lazy=True)

    def __str__(self):
        return self.name


# ======================== STUDENT ========================
class Student(BaseModel):
    __tablename__ = 'students'

    firstName = Column(String(100), nullable=False)
    lastName = Column(String(100), nullable=False)
    birthday = Column(DateTime, nullable=False)
    gender = Column(Boolean, nullable=False)
    parentName = Column(String(255), nullable=False)
    parentPhone = Column(String(20), nullable=False)

    # Thuộc tính trong Python là guardianRelationship,
    # nhưng tên cột trong DB vẫn là "relationship"
    guardianRelationship = Column("relationship", String(50), nullable=False)

    class_id = Column(Integer, ForeignKey('classes.id'), nullable=True)

    health_records = relationship('HealthRecord', backref='student', lazy=True)
    invoices = relationship('Invoice', backref='student', lazy=True)

    def __str__(self):
        return f"{self.lastName} {self.firstName}"

# ===================== HEALTH RECORD =====================
class HealthRecord(BaseModel):
    __tablename__ = 'health_records'

    weight = Column(Float, nullable=False)
    bodyTemperature = Column(Float, nullable=False)
    recordingDate = Column(DateTime, default=datetime.utcnow)
    note = Column(String(255))
    feverWarning = Column(Boolean, default=False)

    student_id = Column(Integer, ForeignKey('students.id'), nullable=False)

    def __str__(self):
        return f"HealthRecord(student={self.student_id}, date={self.recordingDate})"

# ===================== MEAL ATTENDANCE =====================
class MealAttendance(BaseModel):
    __tablename__ = 'meal_attendance'

    student_id = Column(Integer, ForeignKey('students.id'), nullable=False)
    attendance_date = Column(DateTime, nullable=False)
    created_by = Column(Integer, ForeignKey('users.id'))
    note = Column(String(255))

    # Index để tối ưu query
    __table_args__ = (
        Index('idx_student_date', 'student_id', 'attendance_date'),
    )


# ======================= INVOICE =======================
class Invoice(BaseModel):
    __tablename__ = 'invoices'

    # Thời gian áp dụng
    month = Column(Integer, nullable=False)   # 1–12
    year = Column(Integer, nullable=False)

    # Học phí & tiền ăn
    tuition = Column(Float, nullable=True)
    mealDays = Column(Integer, default=0)
    mealFee = Column(Float, nullable=True)
    total = Column(Float, nullable=True)

    # Thanh toán
    paymentDate = Column(DateTime, nullable=True)

    # Quan hệ
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False)
    teacher_id = Column(Integer, ForeignKey('users.id'), nullable=True)

    createdAt = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('student_id', 'month', 'year',
                            name='unique_student_invoice_per_month'),
    )

    def is_paid(self):
        return self.paymentDate is not None

    def __str__(self):
        return f"Invoice(student={self.student_id}, {self.month}/{self.year})"


# ======================= SYSTEM CONFIG =======================
class SystemConfig(BaseModel):
    __tablename__ = 'system_configs'

    key = Column(String(50), nullable=False, unique=True)
    value = Column(Numeric(10, 2), nullable=False)
    note = Column(String(255))
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __str__(self):
        return f"SystemConfig(key={self.key}, value={self.value})"


# ================== CREATE DATABASE ==================
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        import hashlib
        u = User(
            firstName='Tri',
            lastName='Nguyen',
            username='admin',
            password=str(hashlib.md5('123456'.encode('utf-8')).hexdigest()),
            email='admin@school.edu.vn',
            user_role=UserRole.ADMIN
        )
        db.session.add(u)
        db.session.commit()