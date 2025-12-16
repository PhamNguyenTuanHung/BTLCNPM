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
            const card = $(`.student-card[data-id="${btn.dataset.id}"]`);
            if (!card) return;

            openModal({
                id: btn.dataset.id,
                name: $(".student-name", card)?.textContent.trim(),
                gender: $(".gender-tag", card)?.textContent.trim(),
                parent: $(".parent-info p:nth-child(1)", card)?.textContent.replace("Phụ huynh: ", "").trim(),
                phone: $(".parent-info p:nth-child(2)", card)?.textContent.replace("Điện thoại: ", "").trim(),
                weight: $(".health-details div:nth-child(1) p:nth-child(2)", card)?.textContent.replace(" kg", "").trim(),
                temp: $(".temperature-info p", card)?.textContent.replace("°C", "").trim(),
                note: $(".student-note", card)?.textContent.trim()
            });
        });
    });

    /* ================= SUBMIT HEALTH ================= */
    form.addEventListener("submit", e => {
        e.preventDefault();

        const payload = {
            id: fields.id.value,
            weight: fields.weight.value,
            temp: fields.temp.value,
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
        } else {
            p.textContent = "--°C";
            tag?.remove();
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
        body: JSON.stringify({ invoice_id: invoiceId })
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
    const kw = $("#search-input").value.trim();
    location.href = `/students?keyword=${encodeURIComponent(kw)}&page=1`;
}

function applyDateFilter() {
    const date = $("#record-date").value;
    location.href = `/meal-management?date=${date}&page=1`;
}


