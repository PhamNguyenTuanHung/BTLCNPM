// document.addEventListener('DOMContentLoaded', () => {
//
//     // --- DỮ LIỆU GIẢ LẬP (Không thay đổi) ---
//     const studentsData = [
//         { id: 1, name: "Nguyễn Minh An", age: "5 tuổi 8 tháng", gender: "Nam", parent: "Nguyễn Văn A", phone: "0912345678", weight: 15.5, temp: 36.8, tempStatus: "Bình thường" },
//         { id: 2, name: "Trần Thị Bích", age: "5 tuổi 6 tháng", gender: "Nữ", parent: "Trần Văn B", phone: "0987654321", weight: 14.2, temp: 37.8, tempStatus: "Cao" },
//         { id: 3, name: "Lê Hoàng Minh", age: "5 tuổi 4 tháng", gender: "Nam", parent: "Lê Thị C", phone: "0901234567", weight: 16.1, temp: 36.5, tempStatus: "Bình thường" },
//         { id: 4, name: "Phạm Thùy Dung", age: "5 tuổi 9 tháng", gender: "Nữ", parent: "Phạm Văn D", phone: "0909876543", weight: 15.0, temp: 36.9, tempStatus: "Bình thường" },
//         { id: 5, name: "Hoàng Văn Nam", age: "5 tuổi 3 tháng", gender: "Nam", parent: "Hoàng Thị E", phone: "0911122233", weight: 16.5, temp: 37.5, tempStatus: "Cao" },
//     ];
//
//     let currentStudents = [...studentsData];
//
//     // --- DOM ELEMENTS (Thêm các phần tử Modal) ---
//     const studentListContainer = document.getElementById('student-list');
//     const studentCountSpan = document.getElementById('student-count');
//     const searchInput = document.getElementById('search-input');
//     const addStudentBtn = document.getElementById('add-student-btn');
//
//     const editModal = document.getElementById('edit-modal');
//     const closeModalBtn = document.getElementById('close-modal-btn');
//     const cancelModalBtn = document.getElementById('cancel-modal-btn');
//     const editStudentForm = document.getElementById('edit-student-form');
//
//     // Các trường input trong modal
//     const editStudentId = document.getElementById('edit-student-id');
//     const editName = document.getElementById('edit-name');
//     const editParent = document.getElementById('edit-parent');
//     const editPhone = document.getElementById('edit-phone');
//     const editWeight = document.getElementById('edit-weight');
//     const editTemp = document.getElementById('edit-temp');
//
//     // --- UTILITY FUNCTIONS (Giữ nguyên) ---
//
//     // [Hàm getUserIconSVG, getHealthIconSVG, createStudentCardHTML, renderStudentList, handleSearch giữ nguyên]
//
//     // ... [Copy & Paste các hàm Utility từ bản Script.js trước đó vào đây] ...
//
//     // Khởi tạo các hàm Utility cần thiết để chạy
//
//     /**
//      * Tạo SVG Icon cho User
//      */
//     function getUserIconSVG(gender) {
//         const colorClass = gender === 'Nam' ? 'male' : 'female';
//         return `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon-user ${colorClass}">
//                     <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"></path>
//                     <circle cx="12" cy="7" r="4"></circle>
//                 </svg>`;
//     }
//
//     /**
//      * Tạo SVG Icon cho Health (Heart Pulse)
//      */
//     function getHealthIconSVG() {
//         return `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon-health">
//                     <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"></path>
//                     <path d="M3.22 12H9.5l.5-1 2 4.5 2-7 1.5 3.5h5.27"></path>
//                 </svg>`;
//     }
//
//     function getTempStatus(temp) {
//         return temp >= 37.5 ? "Cao" : "Bình thường";
//     }
//
//     /**
//      * Tạo HTML cho một thẻ học sinh
//      */
//     function createStudentCardHTML(student) {
//         const isMale = student.gender === 'Nam';
//         const genderClass = isMale ? 'male' : 'female';
//         const tempStatusText = getTempStatus(student.temp);
//         const tempClass = tempStatusText === 'Bình thường' ? 'normal' : 'high';
//
//         return `
//             <div class="student-card" data-id="${student.id}">
//                 <div class="card-header">
//                     <div class="info-group">
//                         <div class="avatar-wrapper ${genderClass}">
//                             ${getUserIconSVG(student.gender)}
//                         </div>
//                         <div>
//                             <p class="student-name">${student.name}</p>
//                             <p class="student-age">${student.age}</p>
//                         </div>
//                     </div>
//                     <span class="gender-tag ${genderClass}">${student.gender}</span>
//                 </div>
//
//                 <div class="parent-info">
//                     <p><span>Phụ huynh:</span> ${student.parent}</p>
//                     <p><span>Điện thoại:</span> ${student.phone}</p>
//                 </div>
//
//                 <div class="health-box">
//                     <div class="health-header">
//                         ${getHealthIconSVG()}
//                         <span>Sức khỏe gần nhất</span>
//                     </div>
//                     <div class="health-details">
//                         <div>
//                             <p class="detail-label">Cân nặng</p>
//                             <p>${student.weight} kg</p>
//                         </div>
//                         <div>
//                             <p class="detail-label">Nhiệt độ</p>
//                             <div class="temperature-info">
//                                 <p>${student.temp}°C</p>
//                                 <span class="temp-tag ${tempClass}">${tempStatusText}</span>
//                             </div>
//                         </div>
//                     </div>
//                 </div>
//
//                 <div class="card-actions">
//                     <button class="btn-action btn-edit" data-id="${student.id}">
//                         <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon-action">
//                             <path d="M12 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
//                             <path d="M18.375 2.625a1 1 0 0 1 3 3l-9.013 9.014a2 2 0 0 1-.853.505l-2.873.84a.5.5 0 0 1-.62-.62l.84-2.873a2 2 0 0 1 .506-.852z"></path>
//                         </svg>
//                         Sửa
//                     </button>
//                     <button class="btn-action btn-delete" data-id="${student.id}">
//                         <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon-action">
//                             <path d="M3 6h18"></path><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path>
//                             <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path>
//                             <line x1="10" x2="10" y1="11" y2="17"></line><line x1="14" x2="14" y1="11" y2="17"></line>
//                         </svg>
//                         Xóa
//                     </button>
//                 </div>
//             </div>
//         `;
//     }
//
//     /**
//      * Render danh sách học sinh vào DOM
//      */
//     function renderStudentList(students) {
//         studentListContainer.innerHTML = students.map(createStudentCardHTML).join('');
//         studentCountSpan.textContent = `${students.length}/25`;
//         attachEventListeners(); // Gắn lại sự kiện sau khi render mới
//     }
//
//     // Xử lý sự kiện Tìm kiếm
//     function handleSearch() {
//         const query = searchInput.value.toLowerCase().trim();
//         const filteredStudents = studentsData.filter(student =>
//             student.name.toLowerCase().includes(query) ||
//             student.parent.toLowerCase().includes(query)
//         );
//         renderStudentList(filteredStudents);
//     }
//
//     // --- MODAL HANDLERS ---
//
//     /**
//      * Hiển thị modal và điền dữ liệu
//      */
//     function openEditModal(studentId) {
//         const student = studentsData.find(s => s.id === parseInt(studentId));
//         if (student) {
//             editStudentId.value = student.id;
//             editName.value = student.name;
//             editParent.value = student.parent;
//             editPhone.value = student.phone;
//             editWeight.value = student.weight;
//             editTemp.value = student.temp;
//
//             editModal.style.display = 'flex'; // Hiển thị modal
//             editModal.classList.add('active'); // Kích hoạt hiệu ứng scale
//         }
//     }
//
//     /**
//      * Ẩn modal
//      */
//     function closeEditModal() {
//         editModal.style.display = 'none';
//         editModal.classList.remove('active');
//     }
//
//     /**
//      * Xử lý lưu form chỉnh sửa
//      */
//     function handleEditFormSubmit(e) {
//         e.preventDefault();
//
//         const idToUpdate = parseInt(editStudentId.value);
//         const index = studentsData.findIndex(s => s.id === idToUpdate);
//
//         if (index !== -1) {
//             // Cập nhật dữ liệu
//             studentsData[index].name = editName.value;
//             studentsData[index].parent = editParent.value;
//             studentsData[index].phone = editPhone.value;
//             studentsData[index].weight = parseFloat(editWeight.value);
//             studentsData[index].temp = parseFloat(editTemp.value);
//             // Cập nhật trạng thái nhiệt độ tự động
//             studentsData[index].tempStatus = getTempStatus(studentsData[index].temp);
//
//             renderStudentList(studentsData); // Render lại danh sách
//             closeEditModal(); // Đóng modal
//             alert(`Đã cập nhật thông tin trẻ ${studentsData[index].name}.`);
//         }
//     }
//
//     // --- EVENT LISTENERS GỐC ---
//
//     function attachEventListeners() {
//         // Event listeners cho Sửa
//         document.querySelectorAll('.btn-edit').forEach(button => {
//             button.addEventListener('click', (e) => {
//                 const studentId = e.currentTarget.getAttribute('data-id');
//                 openEditModal(studentId); // Gọi hàm hiển thị modal
//             });
//         });
//
//         // Event listeners cho Xóa (giữ nguyên)
//         document.querySelectorAll('.btn-delete').forEach(button => {
//             button.addEventListener('click', (e) => {
//                 const studentId = parseInt(e.currentTarget.getAttribute('data-id'));
//                 const studentName = studentsData.find(s => s.id === studentId)?.name || 'này';
//
//                 if (confirm(`Bạn có chắc chắn muốn xóa trẻ ${studentName} không?`)) {
//                     const index = studentsData.findIndex(s => s.id === studentId);
//                     if (index > -1) {
//                         studentsData.splice(index, 1);
//                         renderStudentList(studentsData);
//                         alert(`Đã xóa trẻ ${studentName}.`);
//                     }
//                 }
//             });
//         });
//
//         // Event listener cho Sidebar (giữ nguyên)
//         document.querySelectorAll('.nav-item').forEach(item => {
//             item.addEventListener('click', (e) => {
//                 document.querySelectorAll('.nav-item').forEach(nav => nav.classList.remove('active'));
//                 e.currentTarget.classList.add('active');
//                 const page = e.currentTarget.getAttribute('data-page');
//                 const contentArea = document.getElementById('main-content-area');
//
//                 if (page !== 'students') {
//                      contentArea.innerHTML = `<div class="p-6"><h2>Trang ${page.charAt(0).toUpperCase() + page.slice(1)}</h2><p>Nội dung đang được phát triển...</p></div>`;
//                 } else {
//                     // Cần re-render lại cấu trúc chính khi quay lại trang students
//                     window.location.reload(); // Cách đơn giản nhất để refresh toàn bộ DOM
//                 }
//             });
//         });
//     }
//
//     // --- GẮN SỰ KIỆN CHUNG & MODAL ---
//
//     // Gắn sự kiện modal
//     closeModalBtn.addEventListener('click', closeEditModal);
//     cancelModalBtn.addEventListener('click', closeEditModal);
//     editModal.addEventListener('click', (e) => {
//         if (e.target === editModal) {
//             closeEditModal(); // Đóng khi click ngoài modal content
//         }
//     });
//
//     // Gắn sự kiện submit form
//     editStudentForm.addEventListener('submit', handleEditFormSubmit);
//
//     // Gắn sự kiện tìm kiếm và nút thêm mới (giữ nguyên)
//     searchInput.addEventListener('input', handleSearch);
//     addStudentBtn.addEventListener('click', () => {
//         alert('Mở form Thêm trẻ mới.');
//     });
//
//     // --- INITIALIZATION ---
//     renderStudentList(currentStudents);
// });
