from QuanLyHocSinh import db, app
from QuanLyHocSinh.model import Class

def create_class(
    name: str,
    semester: int,
    from_year: int,
    to_year: int,
    teacher_id: int
):
    with app.app_context():
        # 1️⃣ Tạo lớp học (sĩ số ban đầu = 0)
        new_class = Class(
            name=name,
            numberStudent=0,      # ⚠️ BẮT BUỘC vì NOT NULL
            semester=semester,
            fromYear=from_year,
            toYear=to_year,
            teacher_id=teacher_id,
            active=True           # kế thừa từ BaseModel
        )

        # 2️⃣ Lưu vào DB
        db.session.add(new_class)
        db.session.commit()

        # 3️⃣ Log kết quả
        print("✅ Tạo lớp học thành công")
        print(f"📚 Tên lớp: {new_class.name}")
        print(f"👶 Sĩ số: {new_class.numberStudent}")
        print(f"📅 Học kỳ: {new_class.semester}")
        print(f"📆 Năm học: {new_class.fromYear} - {new_class.toYear}")
        print(f"👩‍🏫 Giáo viên ID: {new_class.teacher_id}")


if __name__ == "__main__":
    create_class(
        name="Lớp Mầm (2-3 tuổi)",
        semester=1,
        from_year=2025,
        to_year=2026,
        teacher_id=2
    )
