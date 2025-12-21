# Hướng dẫn sử dụng Message Notification Component

## 📋 Tổng quan

Component thông báo (`message.html`) đã được tích hợp vào tất cả các trang HTML của giáo viên trong hệ thống quản lý học sinh. Component này cung cấp thông báo đẹp mắt, hiện đại với 4 loại: success, error, warning, và info.

## 📁 File đã tích hợp

Component đã được chèn vào các file sau:

1. ✅ `student.html` - Danh sách trẻ em
2. ✅ `health-management.html` - Quản lý sức khỏe
3. ✅ `tuition.html` - Quản lý học phí
4. ✅ `meal-management.html` - Quản lý bữa ăn
5. ✅ `statistics.html` - Thống kê
6. ✅ `login.html` - Đăng nhập
7. ✅ `invoice.html` - Hóa đơn

## 🎨 Các loại thông báo

### 1. Success (Thành công) - Màu xanh lá
```javascript
showSuccess("✅ Đã lưu thông tin sức khỏe thành công!");
```

### 2. Error (Lỗi) - Màu đỏ
```javascript
showError("❌ Lỗi khi lưu dữ liệu! Vui lòng thử lại.");
```

### 3. Warning (Cảnh báo) - Màu cam
```javascript
showWarning("⚠️ Nhiệt độ không hợp lệ! Vui lòng kiểm tra lại.");
```

### 4. Info (Thông tin) - Màu xanh dương
```javascript
showInfo("ℹ️ Hệ thống sẽ bảo trì vào 2h sáng mai.");
```

## 💻 Cách sử dụng

### Sử dụng cơ bản

```javascript
// Hiển thị thông báo với thời gian mặc định (3 giây)
showSuccess("Thao tác thành công!");
showError("Có lỗi xảy ra!");
showWarning("Cảnh báo!");
showInfo("Thông tin!");
```

### Tùy chỉnh thời gian hiển thị

```javascript
// Hiển thị trong 5 giây (5000ms)
showSuccess("Thông báo này sẽ hiển thị lâu hơn!", 5000);

// Hiển thị trong 1 giây
showError("Thông báo nhanh!", 1000);
```

### Sử dụng hàm tổng quát

```javascript
// Cú pháp: showMessage(message, type, duration)
showMessage("Nội dung thông báo", "success", 3000);
showMessage("Cảnh báo!", "warning", 4000);
```

## 🔧 Ví dụ thực tế

### Trong form submit

```javascript
fetch('/api/save-data', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(formData)
})
.then(res => res.json())
.then(data => {
    if (data.success) {
        showSuccess("✅ Lưu dữ liệu thành công!");
        // Reload hoặc cập nhật UI
    } else {
        showError("❌ " + data.message);
    }
})
.catch(err => {
    console.error(err);
    showError("❌ Lỗi kết nối server!");
});
```

### Validation trước khi submit

```javascript
function validateForm() {
    if (!name.value) {
        showWarning("⚠️ Vui lòng nhập tên!");
        return false;
    }
    
    if (age.value < 0) {
        showWarning("⚠️ Tuổi không hợp lệ!");
        return false;
    }
    
    return true;
}
```

### Thông báo thông tin

```javascript
// Khi tải trang xong
window.addEventListener('load', () => {
    showInfo("ℹ️ Chào mừng bạn đến với hệ thống!");
});
```

## 🎯 Tính năng

✨ **Animation mượt mà**: Slide in từ phải với hiệu ứng đẹp mắt
📱 **Responsive**: Tự động điều chỉnh trên mobile
🎨 **Gradient hiện đại**: Sử dụng gradient thay vì màu đơn
⏱️ **Progress bar**: Thanh tiến trình tự động đếm ngược
❌ **Đóng thủ công**: Có nút đóng để người dùng tắt sớm
♾️ **Multiple notifications**: Hiển thị nhiều thông báo cùng lúc
🌈 **4 loại thông báo**: Success, Error, Warning, Info

## 📝 Lưu ý

1. **Không cần thêm CSS hoặc JavaScript**: Tất cả đã được tích hợp sẵn trong `message.html`

2. **Thay thế alert()**: Nên thay thế tất cả các `alert()` cũ bằng các hàm mới:
   - `alert("Success!")` → `showSuccess("Success!")`
   - `alert("Error!")` → `showError("Error!")`

3. **Thời gian mặc định**: 3000ms (3 giây). Bạn có thể tùy chỉnh bằng tham số thứ 2

4. **Position**: Thông báo hiển thị ở góc trên bên phải màn hình

5. **Z-index**: Được đặt ở mức 9999 để luôn hiển thị trên cùng

## 🚀 Ví dụ đã cập nhật trong hệ thống

### health-management.html
```javascript
// Trước:
alert("Nhiệt độ không hợp lệ!");

// Sau:
showWarning("⚠️ Nhiệt độ không hợp lệ! Vui lòng kiểm tra lại.");
```

### tuition.html
```javascript
// Trước:
alert('✅ Thanh toán thành công!');

// Sau:
showSuccess('✅ Thanh toán thành công!');
```

### meal-management.html
```javascript
// Trước:
alert('Có lỗi xảy ra khi gửi dữ liệu!');

// Sau:
showError('❌ Có lỗi xảy ra khi gửi dữ liệu!');
```

## 🎨 Customization

Nếu muốn thay đổi style, bạn có thể chỉnh sửa trong `layout/message.html`:

- **Màu sắc**: Thay đổi gradient trong các class `.success`, `.error`, `.warning`, `.info`
- **Vị trí**: Điều chỉnh `top`, `right` trong `.message-container`
- **Thời gian animation**: Thay đổi duration trong `@keyframes`
- **Kích thước**: Điều chỉnh `max-width`, `padding`, `font-size`

---

**Created by**: Message Notification Component
**Version**: 1.0.0
**Date**: 2025-12-20
