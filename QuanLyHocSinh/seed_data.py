from QuanLyHocSinh import app, db, dao
from QuanLyHocSinh.model import (
    User, Class, Student, HealthRecord,
    Invoice, MealAttendance, SystemConfig, UserRole
)
from datetime import datetime, timedelta
import hashlib
import random

def md5(pw):
    return hashlib.md5(pw.encode('utf-8')).hexdigest()




with app.app_context():
    print("⚠️ RESET DATABASE...")
    db.drop_all()
    db.create_all()
    print("✅ Đã xoá & tạo lại toàn bộ database")
    print("🔄 Seeding FULL dữ liệu hệ thống...")

    # ================== SYSTEM CONFIG ==================
    if SystemConfig.query.count() == 0:
        configs = [
            SystemConfig(key='tuition', value=500000, note='Học phí (VND)'),
            SystemConfig(key='mealFee', value=50000, note='Tiền ăn/ngày (VND)'),
            SystemConfig(key='maxNumber', value=25, note='Sĩ số tối đa')
        ]
        db.session.add_all(configs)
        db.session.commit()
        print("✅ Đã tạo SystemConfig")

    tuition = float(SystemConfig.query.filter_by(key='tuition').first().value)
    mealFee = float(SystemConfig.query.filter_by(key='mealFee').first().value)

    # ================== ADMIN ==================

    admin1 = User(
        firstName='Tuan',
        lastName='Hung',
        username='admin1',
        password=md5('123456'),
        email='admin@school.edu.vn',
        user_role=UserRole.ADMIN
    )

    # ================== GIÁO VIÊN ==================
    teacher1 = User(
        firstName='Lan',
        lastName='Tran',
        username='teacher_lan',
        password=md5('123456'),
        email='lan@school.edu.vn',
        user_role=UserRole.TEACHER
    )

    teacher2 = User(
        firstName='Hoa',
        lastName='Pham',
        username='teacher_hoa',
        password=md5('123456'),
        email='hoa@school.edu.vn',
        user_role=UserRole.TEACHER
    )

    db.session.add_all([admin1,teacher1, teacher2])
    db.session.commit()

    # ================== LỚP ==================
    class1 = Class(
        name='Lớp Lá 1',
        numberStudent=20,
        semester=1,
        fromYear=2024,
        toYear=2025,
        teacher_id=teacher1.id
    )

    class2 = Class(
        name='Lớp Chồi 2',
        numberStudent=25,
        semester=1,
        fromYear=2024,
        toYear=2025,
        teacher_id=teacher2.id
    )

    class3 = Class(
        name='Lớp Chồi 3',
        numberStudent=23,
        semester=1,
        fromYear=2024,
        toYear=2025,
        teacher_id=teacher2.id
    )

    db.session.add_all([class1, class2,class3])
    db.session.commit()

    # ================== HỌC SINH ==================
    first_names = ['An', 'Bình', 'Chi', 'Dũng', 'Hà', 'Huy', 'Khánh', 'Linh',
                   'Minh', 'My', 'Nam', 'Ngọc', 'Phúc', 'Quân', 'Trang']
    last_names = ['Nguyen', 'Tran', 'Le', 'Pham', 'Hoang']
    relationships = ['Cha', 'Mẹ', 'Ông', 'Bà']

    def create_students(class_id, count):
        students = []
        for _ in range(count):
            students.append(
                Student(
                    firstName=random.choice(first_names),
                    lastName=random.choice(last_names),
                    birthday=datetime(2019, random.randint(1, 12), random.randint(1, 28)),
                    gender=random.choice([True, False]),
                    parentName=f"{random.choice(last_names)} Van {random.choice(first_names)}",
                    parentPhone=f"09{random.randint(10000000, 99999999)}",
                    guardianRelationship=random.choice(relationships),
                    class_id=class_id
                )
            )
        return students

    students = create_students(class1.id, 20) + create_students(class2.id, 25) + create_students(class3.id, 23)
    db.session.add_all(students)
    db.session.commit()

    # ================== HEALTH RECORD ==================
    health_records = []
    for s in students:
        health_records.append(
            HealthRecord(
                weight=round(random.uniform(14, 22), 1),
                bodyTemperature=round(random.uniform(36.2, 37.5), 1),
                recordingDate=datetime.utcnow() - timedelta(days=random.randint(0, 10)),
                feverWarning=False,
                student_id=s.id
            )
        )

    db.session.add_all(health_records)
    db.session.commit()
    print("✅ Đã tạo HealthRecord")

    from datetime import date
    today = date.today()
    month = today.month
    year = today.year
    import random

    import calendar
    from datetime import date

    meal_records = []

    days_in_month = calendar.monthrange(year, month)[1]
    today = date.today()

    for s in students:
        meal_days_target = random.randint(20, 26)
        count = 0

        for day in range(1, days_in_month + 1):
            d = date(year, month, day)

            if d.weekday() == 6 or d >= today:
                continue

            # 80% xác suất có ăn
            ate_today = random.random() < 0.8
            if ate_today:
                meal_records.append(
                    MealAttendance(
                        student_id=s.id,
                        attendance_date=datetime.combine(d, datetime.min.time()),
                        created_by=s.class_.teacher_id,
                        note=None
                    )
                )
                count += 1

            if count >= meal_days_target:
                break

    db.session.add_all(meal_records)
    db.session.commit()
    print("✅ Đã tạo MealAttendance")


    # ================== INVOICE ==================
    invoices = []

    for s in students:
        existed = Invoice.query.filter_by(
            student_id=s.id,
            month=month,
            year=year
        ).first()

        if existed:
            continue

        meal_days = dao.count_meal_days(student_id=s.id, month=month, year=year)
        print(meal_days)

        invoices.append(
            Invoice(
                month=month,
                year=year,
                mealDays=meal_days,
                mealFee=mealFee,
                tuition=tuition,
                total=None,
                paymentDate=None,
                student_id=s.id,
                teacher_id=s.class_.teacher_id
            )
        )

    db.session.add_all(invoices)
    db.session.commit()
    print("✅ Đã tạo Invoice tháng", month, "/", year)

    print("\n🎉 HOÀN TẤT SEED FULL DATABASE")
    print("👩1 admin|‍🏫 3 giáo viên | 🏫 3 lớp | 👶 68 học sinh")
    print("🩺 HealthRecord | 💰 Invoice | ⚙ SystemConfig")
