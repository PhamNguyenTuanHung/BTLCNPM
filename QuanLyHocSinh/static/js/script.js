document.addEventListener("DOMContentLoaded", () => {

    const editButtons = document.querySelectorAll(".btn-edit");
    const deleteButtons = document.querySelectorAll(".btn-delete");

    // const addButton = document.getElementById("add-student-btn");

    const studentModal = document.getElementById("student-modal");
    const studentForm = document.getElementById("student-form");
    const modalTitle = document.getElementById("modal-title");

    const closeBtn = document.getElementById("close-modal-btn");
    const cancelBtn = document.getElementById("cancel-modal-btn");

    const studentIdInput = document.getElementById("student-id");
    const studentName = document.getElementById("student-name");
    const studentGender = document.getElementById("student-gender");
    const studentParent = document.getElementById("student-parent");
    const studentPhone = document.getElementById("student-phone");
    const studentWeight = document.getElementById("student-weight");
    const studentTemp = document.getElementById("student-temp");


    // ==== OPEN MODAL ====
    function openModal(mode, studentData = null) {
        studentModal.style.display = "flex";
        studentModal.classList.add("active");
        studentForm.dataset.mode = mode;

        if (mode === "edit" && studentData) {
            modalTitle.textContent = "Chỉnh sửa thông tin trẻ";
            studentIdInput.value = studentData.id;
            studentName.value = studentData.name;
            studentGender.value = studentData.gender;
            studentParent.value = studentData.parent;
            studentPhone.value = studentData.phone;
            studentWeight.value = studentData.weight;
            studentTemp.value = studentData.temp;
        } else {
            modalTitle.textContent = "Thêm trẻ mới";
            studentForm.reset();
            studentIdInput.value = "";
        }
    }

    // === CLOSE MODAL ===
    function closeModal() {
        studentModal.style.display = "none";
        studentModal.classList.remove("active");
    }

    closeBtn.addEventListener("click", closeModal);
    cancelBtn.addEventListener("click", closeModal);

    // === ADD BUTTON ===
    // addButton.addEventListener("click", () => openModal("add"));

    // === EDIT BUTTONS ===
    editButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const id = btn.dataset.id;
            const card = document.querySelector(`.student-card[data-id="${id}"]`);
            if (!card) return console.warn("Không tìm thấy thẻ học sinh với ID:", id);

            // Lấy weight và temp, xử lý trường hợp '--'
            const weightText = card.querySelector(".health-details div:nth-child(1) p:nth-child(2)")?.textContent.replace(" kg", "").trim() || "";
            const tempText = card.querySelector(".temperature-info p")?.textContent.replace("°C", "").trim() || "";

            const studentData = {
                id: id,
                name: card.querySelector(".student-name")?.textContent.trim() || "",
                gender: card.querySelector(".gender-tag")?.textContent.trim() || "",
                parent: card.querySelector(".parent-info p:nth-child(1)")?.textContent.replace("Phụ huynh: ", "").trim() || "",
                phone: card.querySelector(".parent-info p:nth-child(2)")?.textContent.replace("Điện thoại: ", "").trim() || "",
                weight: weightText === '--' ? '' : weightText,
                temp: tempText === '--' ? '' : tempText
            };
            openModal("edit", studentData);
        });
    });

    // === SUBMIT FORM ===
    studentForm.addEventListener("submit", e => {
        e.preventDefault();
        const mode = studentForm.dataset.mode;
        const studentData = {
            id: studentIdInput.value,
            name: studentName.value,
            gender: studentGender.value,
            parent: studentParent.value,
            phone: studentPhone.value,
            weight: studentWeight.value,
            temp: studentTemp.value
        };

        if (mode === "edit") {
            // PUT request
            fetch("http://127.0.0.1:5000/students", {
                method: "PUT",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify(studentData)
            })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        const card = document.querySelector(`.student-card[data-id="${studentData.id}"]`);
                        if (!card) return;

                        // Cập nhật card
                        card.querySelector(".student-name").textContent = studentData.name;
                        card.querySelector(".parent-info p:nth-child(1)").innerHTML = `<span>Phụ huynh:</span> ${studentData.parent}`;
                        card.querySelector(".parent-info p:nth-child(2)").innerHTML = `<span>Điện thoại:</span> ${studentData.phone}`;
                        card.querySelector(".health-details div:nth-child(1) p:nth-child(2)").textContent = `${studentData.weight} kg`;

                        const tempP = card.querySelector(".temperature-info p");
                        const tempTag = card.querySelector(".temperature-info .temp-tag");
                        tempP.textContent = `${studentData.temp}°C`;
                        const status = parseFloat(studentData.temp) >= 37.5 ? "Cao" : "Bình thường";
                        tempTag.textContent = status;
                        tempTag.className = `temp-tag ${status === "Cao" ? "high" : "normal"}`;

                        // Gender
                        const genderTag = card.querySelector(".gender-tag");
                        const avatarWrapper = card.querySelector(".avatar-wrapper");
                        const iconUser = card.querySelector(".icon-user");
                        const genderClass = studentData.gender === "Nam" ? "male" : "female";
                        genderTag.textContent = studentData.gender;
                        genderTag.className = `gender-tag ${genderClass}`;
                        avatarWrapper.className = `avatar-wrapper ${genderClass}`;
                        iconUser.classList.remove("male", "female");
                        iconUser.classList.add(genderClass);

                        closeModal();
                        alert("Cập nhật thành công!");
                    } else {
                        alert("Có lỗi khi cập nhật học sinh.");
                    }
                })
                .catch(err => console.error(err));
        } else {
            // POST request - thêm mới
            fetch("/students", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify(studentData)
            })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        alert("Thêm học sinh thành công!");
                        closeModal();
                        location.reload();
                    } else {
                        alert("Có lỗi khi thêm học sinh.");
                    }
                })
                .catch(err => console.error(err));
        }
    });


    // ==== CLOSE MODAL ====
    document.getElementById("close-modal-btn").addEventListener("click", () => {
        editModal.style.display = "none";
        editModal.classList.remove("active");
    });

    document.getElementById("cancel-modal-btn").addEventListener("click", () => {
        editModal.style.display = "none";
        editModal.classList.remove("active");
    });

    // === CLICK OUTSIDE TO CLOSE ===
    studentModal.addEventListener("click", (e) => {
        if (e.target === studentModal) {
            studentModal.style.display = "none";
            studentModal.classList.remove("active");
        }
    });
    // === XÓA HỌC SINH ===

    deleteButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const id = btn.dataset.id;
            const card = document.querySelector(`.student-card[data-id="${id}"]`);
            const name = card.querySelector(".student-name").textContent;

            if (confirm(`Bạn có chắc muốn xóa trẻ ${name}? `)) {
                card.remove();
            }
        });
    });

    // JS

});

function updateHealth(btn) {
    const card = btn.closest('.student-health-card');
    const id = card.dataset.studentId;

    const weightInput = card.querySelector('.input-weight');
    const tempInput = card.querySelector('.input-temp');
    const noteInput = card.querySelector('.input-note');

    const weight = parseFloat(weightInput.value);
    const temp = parseFloat(tempInput.value);
    const note = noteInput.value.trim();

    // Validate
    if (isNaN(weight) || weight <= 0) {
        alert("Cân nặng không hợp lệ!");
        return;
    }
    if (isNaN(temp) || temp <= 30 || temp >= 45) {
        alert("Nhiệt độ không hợp lệ!");
        return;
    }
    if (note.length > 200) {
        alert("Ghi chú quá dài (tối đa 200 ký tự)!");
        return;
    }

    // POST dữ liệu
    fetch("/health-management", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({id, weight, temp, note})
    })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                alert("Đã lưu thành công!");

                // === CẬP NHẬT TRẠNG THÁI TRÊN GIAO DIỆN ===
                const statusCol = card.querySelector('.status-col .status-indicator');
                if (!statusCol) return;

                if (temp >= 37.5) {
                    statusCol.textContent = "Cao";
                    statusCol.classList.add("status-high");
                    statusCol.classList.remove("status-normal");
                } else {
                    statusCol.textContent = "Bình thường";
                    statusCol.classList.add("status-normal");
                    statusCol.classList.remove("status-high");
                }

                // Thêm class input nếu muốn highlight nhiệt độ cao
                tempInput.classList.toggle("status-high-input", temp >= 37.5);
            }
        }).catch(err => console.error("Error:", err));
}

function payStudentTuition(btn) {
    const card = btn.closest('.student-tuition-card');
    if (!card) return;

    const invoiceId = card.dataset.invoiceId;
    if (!invoiceId) {
        alert("Không tìm thấy hóa đơn!");
        return;
    }

    if (!confirm("Xác nhận đóng học phí cho học sinh này?")) return;

    // Khóa nút ngay khi click (chống spam)
    btn.disabled = true;
    const originalText = btn.textContent;
    btn.textContent = "Đang xử lý...";

    fetch("/api/invoices/pay", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({invoice_id: invoiceId})
    })
        .then(res => {
            if (!res.ok) throw new Error("Network error");
            return res.json();
        })
        .then(data => {
            if (!data.success) {
                throw new Error(data.message || "Thanh toán thất bại!");
            }

            // ===== UPDATE UI =====
            const statusEl = card.querySelector(".tuition-status");
            if (statusEl) {
                statusEl.textContent = "Đã thanh toán";
                statusEl.classList.remove("status-unpaid", "text-danger");
                statusEl.classList.add("status-paid", "text-success");
            }

            btn.textContent = "Xuất HĐ";
            btn.classList.add("btn-action-fee", "btn-export-invoice");

            // (Tuỳ chọn) hiện toast thay vì alert
            alert("✅ Đã đóng học phí!");
        })
        .catch(err => {
            console.error(err);
            alert(err.message || "Lỗi kết nối server!");
            btn.disabled = false;
            btn.textContent = originalText;
        });
}


function searchStudents() {
    const keyword = document.getElementById("search-input").value.trim();
    const params = new URLSearchParams(window.location.search);
    params.set("keyword", keyword);
    params.set("page", 1);

    window.location.href = `/students?${params.toString()}`;
}


