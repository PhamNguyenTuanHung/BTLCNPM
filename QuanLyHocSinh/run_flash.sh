echo "--- Cài thư viện ---"
pip install -r requirements.txt

echo "-- Tạo dữ liệu ---"
python -m QuanLyHocSinh.model

echo "-- Chạy ứng dụng ---"
 python -m QuanLyHocSinh.index