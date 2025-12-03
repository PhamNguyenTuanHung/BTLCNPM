document.addEventListener("DOMContentLoaded", () => {

    const searchInput = document.getElementById("search-input");
    const editButtons = document.querySelectorAll(".btn-edit");
    const deleteButtons = document.querySelectorAll(".btn-delete");

    const addButton = document.getElementById("add-student-btn");

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
    addButton.addEventListener("click", () => openModal("add"));

    // === EDIT BUTTONS ===
    editButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const id = btn.dataset.id;
            const card = document.querySelector(`.student-card[data-id="${id}"]`);
            if (!card) return console.warn("Không tìm thấy thẻ học sinh với ID:", id);

            const studentData = {
                id: id,
                name: card.querySelector(".student-name")?.textContent.trim() || "",
                gender: card.querySelector(".gender-tag")?.textContent.trim() || "",
                parent: card.querySelector(".parent-info p:nth-child(1)")?.textContent.replace("Phụ huynh: ", "").trim() || "",
                phone: card.querySelector(".parent-info p:nth-child(2)")?.textContent.replace("Điện thoại: ", "").trim() || "",
                weight: card.querySelector(".health-details div:nth-child(1) p:nth-child(2)")?.textContent.replace(" kg", "").trim() || "",
                temp: card.querySelector(".temperature-info p")?.textContent.replace("°C", "").trim() || ""
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

    // === SEARCH STUDENT ===
    function searchStudents() {
        const keyword = searchInput.value.toLowerCase().trim();
        const studentCards = document.querySelectorAll(".student-card");

        studentCards.forEach(card => {
            const name = card.querySelector(".student-name")?.textContent.toLowerCase() || "";
            if (name.includes(keyword)) {
                card.style.display = "";
            } else {
                card.style.display = "none";
            }
        });
    }

    searchInput.addEventListener("input", searchStudents);

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

    function updateDailyMeals() {

    }

});



