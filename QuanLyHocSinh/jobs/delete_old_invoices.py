"""
Scheduled job to auto-delete old invoices
Run this script daily via cron/scheduler
"""
from datetime import datetime, timedelta
from QuanLyHocSinh import app, db
from QuanLyHocSinh.model import Invoice

def delete_old_invoices():
    """
    Xóa hóa đơn sau 7 ngày kể từ ngày thanh toán
    """
    with app.app_context():
        # Tính ngày 7 ngày trước
        seven_days_ago = datetime.now() - timedelta(days=7)
        
        # Tìm các invoice đã thanh toán > 7 ngày
        old_invoices = Invoice.query.filter(
            Invoice.paymentDate.isnot(None),
            Invoice.paymentDate < seven_days_ago,
            Invoice.active == True
        ).all()
        
        deleted_count = 0
        for invoice in old_invoices:
            # Soft delete
            invoice.active = False
            deleted_count += 1
        
        db.session.commit()
        print(f"Deleted {deleted_count} old invoices (payment date < {seven_days_ago.date()})")

if __name__ == '__main__':
    delete_old_invoices()
