document.addEventListener("DOMContentLoaded", () => {
    const $ = (s, p = document) => p.querySelector(s);
    const $$ = (s, p = document) => [...p.querySelectorAll(s)];

    /* ================= MODAL ================= */
    const modal = $("#student-modal");
    const form = $("#student-form");

    const fields = {
        id: $("#student-id"),
        name: $("#student-name"),
        gender: $("#student-gender"),
        parent: $("#student-parent"),
        phone: $("#student-phone"),
        weight: $("#student-weight"),
        temp: $("#student-temp"),
        note: $("#student-note")
    };

    const openModal = (data = {}) => {
        modal.classList.add("active");
        modal.style.display = "flex";
        Object.keys(fields).forEach(k => fields[k].value = data[k] || "");
    };

    const closeModal = () => {
        modal.classList.remove("active");
        modal.style.display = "none";
    };

    $("#close-modal-btn")?.addEventListener("click", closeModal);
    $("#cancel-modal-btn")?.addEventListener("click", closeModal);
    modal.addEventListener("click", e => e.target === modal && closeModal());

    /* ================= EDIT ================= */
    $$(".btn-edit").forEach(btn => {
        btn.addEventListener("click", () => {

            const card = document.querySelector(
                `.student-card[data-id="${btn.dataset.id}"]`
            );
            if (!card) return;

            /* ===== GENDER ===== */
            const genderText =
                card.querySelector(".gender-tag")?.textContent.trim();

            /* ===== AVATAR ===== */
            const avatar = document.querySelector("#modal-avatar");
            avatar.className = `avatar-wrapper ${genderText === "Nam" ? "male" : "female"}`;
            avatar.innerHTML = card.querySelector(".icon-user").outerHTML;

            /* ===== TEXT INFO ===== */
            document.querySelector("#modal-name").textContent =
                card.querySelector(".student-name")?.textContent || "";

            document.querySelector("#modal-age").textContent =
                card.querySelector(".student-age")?.textContent || "";

            document.querySelector("#modal-gender").textContent = genderText || "";

            document.querySelector("#modal-parent").textContent =
                card.querySelector(".parent-info p:nth-child(1)")
                    ?.textContent.replace("Phụ huynh:", "").trim() || "";

            document.querySelector("#modal-phone").textContent =
                card.querySelector(".parent-info p:nth-child(2)")
                    ?.textContent.replace("Điện thoại:", "").trim() || "";

            /* ===== INPUT ===== */
            document.querySelector("#student-id").value = btn.dataset.id;

            document.querySelector("#student-weight").value =
                card.querySelector(".health-details div:nth-child(1) p:nth-child(2)")
                    ?.textContent.replace("kg", "").trim() || "";

            document.querySelector("#student-temp").value =
                card.querySelector(".temperature-info p")
                    ?.textContent.replace("°C", "").trim() || "";
            // ===== ĐỔ MÀU KHUNG NẾU SỐT =====
            const tempVal = parseFloat($("#student-temp").value);
            const healthBox = document.querySelector(".modal-content .health-box");

            // reset trạng thái cũ
            healthBox.classList.remove("fever");

            // nếu sốt
            if (!isNaN(tempVal) && tempVal >= 37.5) {
                healthBox.classList.add("fever");
            }

            document.querySelector("#student-note").value = "";

            /* ===== OPEN MODAL ===== */
            modal.classList.add("active");
            modal.style.display = "flex";
        });
    });

    /* ================= SUBMIT HEALTH ================= */
    form.addEventListener("submit", e => {
        e.preventDefault();

        const weight = fields.weight.value.trim();
        const temp = fields.temp.value.trim();

        // reset lỗi
        fields.weight.classList.remove("error");
        fields.temp.classList.remove("error");

        // ===== CHECK RỖNG =====
        if (!weight || !temp) {
            alert("Vui lòng nhập đầy đủ cân nặng và nhiệt độ");
            if (!weight) fields.weight.classList.add("error");
            if (!temp) fields.temp.classList.add("error");
            return;
        }

        // ===== CHECK GIÁ TRỊ =====
        if (weight <= 0 || temp <= 0) {
            alert("Giá trị nhập không hợp lệ");
            fields.weight.classList.add("error");
            fields.temp.classList.add("error");
            return;
        }

        // ===== CHECK NHIỆT ĐỘ HỢP LÝ =====
        if (temp < 34 || temp > 42) {
            alert("Nhiệt độ không hợp lý (34°C – 42°C)");
            fields.temp.classList.add("error");
            return;
        }

        // ===== OK → GỬI SERVER =====
        const payload = {
            id: fields.id.value,
            weight,
            temp,
            note: fields.note.value
        };

        fetch("/health-management", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(payload)
        })
            .then(r => r.json())
            .then(res => {
                if (!res.success) throw "Cập nhật thất bại";
                updateHealthCard(payload);
                closeModal();
                alert("✅ Cập nhật thành công");
            })
            .catch(err => alert(err));
    });

    const updateHealthCard = ({id, weight, temp}) => {
        const card = $(`.student-card[data-id="${id}"]`);
        if (!card) return;

        $(".health-details div:nth-child(1) p:nth-child(2)", card).textContent =
            weight ? `${weight} kg` : "-- kg";

        const tempBox = $(".temperature-info", card);
        if (!tempBox) return;

        let p = $("p", tempBox) || tempBox.prepend(document.createElement("p"));
        let tag = $(".temp-tag", tempBox);

        if (temp) {
            const high = parseFloat(temp) >= 37.5;
            p.textContent = `${temp}°C`;
            if (!tag) {
                tag = document.createElement("span");
                tag.className = "temp-tag";
                tempBox.appendChild(tag);
            }
            tag.textContent = high ? "Cao" : "Bình thường";
            tag.className = `temp-tag ${high ? "high" : "normal"}`;
            card.classList.toggle("fever", high);

        } else {
            p.textContent = "--°C";
            tag?.remove();
            card.classList.remove("fever");

        }
    };

    /* ================= DELETE ================= */
    $$(".btn-delete").forEach(btn => {
        btn.addEventListener("click", () => {
            const card = $(`.student-card[data-id="${btn.dataset.id}"]`);
            const name = $(".student-name", card)?.textContent;
            if (confirm(`Xóa trẻ ${name}?`)) card.remove();
        });
    });
});

/* ================= TUITION ================= */
function payStudentTuition(btn) {
    const card = btn.closest(".student-tuition-card");
    const invoiceId = card?.dataset.invoiceId;
    if (!invoiceId || !confirm("Xác nhận đóng học phí?")) return;

    btn.disabled = true;

    fetch("/api/invoices/pay", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({invoice_id: invoiceId})
    })
        .then(r => r.json())
        .then(res => {
            if (!res.success) throw res.message;

            // ✅ Update status
            const statusEl = card.querySelector(".tuition-status");
            if (statusEl) {
                statusEl.textContent = "Đã thanh toán";
                statusEl.classList.remove("text-danger", "status-unpaid");
                statusEl.classList.add("text-success", "status-paid");
            }

            // ✅ Replace action button
            btn.parentElement.innerHTML = `
                <a href="/invoice/${invoiceId}"
                   class="btn-action-fee btn-export-invoice">
                    Xuất HĐ
                </a>
            `;
        })
        .catch(err => alert(err))
        .finally(() => btn.disabled = false);
}

/* ================= FILTER ================= */
function searchStudents() {
    const kw = document.getElementById("search-input").value.trim();
    window.location.href =
        `/students?keyword=${encodeURIComponent(kw)}&page=1`;
}

function applyDateFilter() {
    const date = $("#record-date").value;
    location.href = `/meal-management?date=${date}&page=1`;
}


