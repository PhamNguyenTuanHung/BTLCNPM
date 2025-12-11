"""
Script để migrate bảng SystemConfig sang cấu trúc mới
Chạy: python migrate_systemconfig.py
"""
from QuanLyHocSinh import app, db
from QuanLyHocSinh.model import SystemConfig
from sqlalchemy import text

def migrate_systemconfig():
    """
    Migration cho bảng SystemConfig từ cấu trúc cũ sang cấu trúc mới
    """
    with app.app_context():
        print("🔄 Bắt đầu migration bảng SystemConfig...")
        
        try:
            # Kiểm tra xem bảng cũ có dữ liệu không
            old_data = db.session.execute(text("""
                SELECT id, tuition, maxNumber, mealFee, effectiveDate, createdAt, updatedAt, active 
                FROM system_configs
            """)).fetchall()
            
            print(f"📊 Tìm thấy {len(old_data)} bản ghi cũ")
            
            # Backup data cũ
            backup_configs = []
            for row in old_data:
                backup_configs.append({
                    'id': row[0],
                    'tuition': row[1],
                    'maxNumber': row[2],
                    'mealFee': row[3],
                    'effectiveDate': row[4],
                    'createdAt': row[5],
                    'updatedAt': row[6],
                    'active': row[7]
                })
            
            print("💾 Đã backup dữ liệu cũ")
            
        except Exception as e:
            print(f"⚠️ Không tìm thấy dữ liệu cũ hoặc bảng chưa tồn tại: {e}")
            backup_configs = []
        
        # Drop bảng cũ
        print("🗑️ Xóa bảng cũ...")
        db.session.execute(text("DROP TABLE IF EXISTS system_configs"))
        db.session.commit()
        
        # Tạo bảng mới
        print("✨ Tạo bảng mới với cấu trúc mới...")
        SystemConfig.__table__.create(db.engine, checkfirst=True)
        
        # Chuyển đổi dữ liệu cũ sang cấu trúc mới
        if backup_configs:
            print("📝 Chuyển đổi dữ liệu...")
            for config in backup_configs:
                # Tạo 3 bản ghi mới từ 1 bản ghi cũ
                configs_to_add = [
                    SystemConfig(
                        key='tuition',
                        value=float(config['tuition']),
                        note='Học phí (VND)',
                        createdAt=config['createdAt'],
                        updatedAt=config['updatedAt'],
                        active=config['active']
                    ),
                    SystemConfig(
                        key='maxNumber',
                        value=float(config['maxNumber']),
                        note='Sĩ số tối đa',
                        createdAt=config['createdAt'],
                        updatedAt=config['updatedAt'],
                        active=config['active']
                    ),
                    SystemConfig(
                        key='mealFee',
                        value=float(config['mealFee']),
                        note='Phí ăn/ngày (VND)',
                        createdAt=config['createdAt'],
                        updatedAt=config['updatedAt'],
                        active=config['active']
                    )
                ]
                
                for new_config in configs_to_add:
                    db.session.add(new_config)
            
            db.session.commit()
            print(f"✅ Đã chuyển đổi {len(backup_configs)} bản ghi cũ thành {len(backup_configs) * 3} bản ghi mới")
        else:
            # Thêm dữ liệu mặc định nếu chưa có
            print("📝 Thêm dữ liệu cấu hình mặc định...")
            default_configs = [
                SystemConfig(key='tuition', value=5000000.0, note='Học phí (VND)', active=True),
                SystemConfig(key='maxNumber', value=40.0, note='Sĩ số tối đa', active=True),
                SystemConfig(key='mealFee', value=50000.0, note='Phí ăn/ngày (VND)', active=True)
            ]
            
            for config in default_configs:
                db.session.add(config)
            
            db.session.commit()
            print("✅ Đã thêm 3 cấu hình mặc định")
        
        # Kiểm tra kết quả
        new_count = SystemConfig.query.count()
        print(f"\n🎉 Migration hoàn tất! Hiện có {new_count} cấu hình trong hệ thống")
        
        # Hiển thị dữ liệu mới
        print("\n📋 Dữ liệu hiện tại:")
        for config in SystemConfig.query.all():
            print(f"  - {config.key}: {config.value} ({config.note})")

if __name__ == '__main__':
    migrate_systemconfig()
