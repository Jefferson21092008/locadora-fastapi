import {
    ApiError,
    Permissions,
    applyNavigationPermissions,
    clearToken,
    createFinancialPayment,
    getCurrentUser,
    getFinancialAccounts,
    getRentalFinancialSummary,
    hasPermission,
    logout,
    restoreSession,
    reverseFinancialPayment,
} from "/app/js/api.js";

const roleBadge = document.querySelector("#current-role");
const logoutButton = document.querySelector("#logout-button");
const message = document.querySelector("#finance-message");
const searchInput = document.querySelector("#finance-search");
const refreshButton = document.querySelector("#finance-refresh");
const list = document.querySelector("#finance-list");
const prevButton = document.querySelector("#finance-prev");
const nextButton = document.querySelector("#finance-next");
const pageLabel = document.querySelector("#finance-page");
const detail = document.querySelector("#finance-detail");
const totalDue = document.querySelector("#finance-total-due");
const totalPaid = document.querySelector("#finance-total-paid");
const balance = document.querySelector("#finance-balance");
const deposit = document.querySelector("#finance-deposit");
const components = document.querySelector("#finance-components");
const paymentForm = document.querySelector("#finance-payment-form");
const paymentValue = document.querySelector("#finance-payment-value");
const paymentMethod = document.querySelector("#finance-payment-method");
const paymentInstallments = document.querySelector("#finance-payment-installments");
const paymentNotes = document.querySelector("#finance-payment-notes");
const payments = document.querySelector("#finance-payments");

let currentUser = null;
let page = 1;
let totalPages = 0;
let selectedRentalId = null;
let summary = null;
let searchTimer = null;

function goToLogin() {
    window.location.replace("/app/");
}

function can(permission) {
    return hasPermission(currentUser, permission);
}

function formatCurrency(value) {
    return Number(value ?? 0).toLocaleString(
        "pt-BR",
        {
            style: "currency",
            currency: "BRL",
        },
    );
}

function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function showMessage(text, type = "error") {
    message.textContent = text;
    message.dataset.type = type;
}

function clearMessage() {
    message.textContent = "";
    delete message.dataset.type;
}

function renderAccounts(data) {
    totalPages = data.total_paginas;
    pageLabel.textContent = (
        totalPages > 0
            ? `Página ${data.pagina} de ${totalPages}`
            : "Nenhuma página"
    );
    prevButton.disabled = data.pagina <= 1;
    nextButton.disabled = (
        data.pagina >= totalPages
        || totalPages === 0
    );

    if (data.items.length === 0) {
        list.innerHTML = `
            <p class="inspection-records__empty">Nenhuma conta financeira encontrada.</p>
        `;
        return;
    }

    list.innerHTML = data.items.map((item) => `
        <article class="inspection-record">
            <div>
                <strong>#${item.aluguel_id} · ${escapeHtml(item.cliente_nome)}</strong>
                <span>${escapeHtml(item.veiculo)} · ${item.status_financeiro}</span>
                <span>${formatCurrency(item.total_pago)} pagos de ${formatCurrency(item.total_devido)}</span>
            </div>
            <button class="secondary-button" type="button" data-finance-rental="${item.aluguel_id}">
                Abrir
            </button>
        </article>
    `).join("");

    for (const button of list.querySelectorAll("[data-finance-rental]")) {
        button.addEventListener("click", async () => {
            selectedRentalId = Number(
                button.dataset.financeRental
            );
            await loadSummary();
        });
    }
}

function renderPayments() {
    if (summary.pagamentos.length === 0) {
        payments.innerHTML = `
            <p class="inspection-records__empty">Nenhum pagamento adicional registrado.</p>
        `;
        return;
    }

    payments.innerHTML = summary.pagamentos.map((item) => `
        <article class="inspection-record ${item.status === "estornado" ? "inspection-record--muted" : ""}">
            <div>
                <strong>${formatCurrency(item.valor)} · ${escapeHtml(item.forma)}</strong>
                <span>${item.parcelas}x · ${item.status}</span>
                <p>${escapeHtml(item.observacoes ?? "Sem observações.")}</p>
            </div>
            ${item.status === "confirmado" && can(Permissions.FINANCEIRO_ESTORNAR) ? `
                <button class="text-button" type="button" data-reverse-payment="${item.id}">
                    Estornar
                </button>
            ` : ""}
        </article>
    `).join("");

    for (const button of payments.querySelectorAll("[data-reverse-payment]")) {
        button.addEventListener("click", async () => {
            try {
                await reverseFinancialPayment(
                    Number(button.dataset.reversePayment)
                );
                await loadSummary();
                await loadAccounts();
                showMessage(
                    "Pagamento estornado.",
                    "success",
                );
            } catch (error) {
                showMessage(error.message);
            }
        });
    }
}

function renderSummary() {
    detail.hidden = false;
    totalDue.textContent = formatCurrency(summary.total_devido);
    totalPaid.textContent = formatCurrency(summary.total_pago);
    balance.textContent = formatCurrency(summary.saldo_pendente);
    deposit.textContent = formatCurrency(
        summary.caucao_retida_disponivel
    );

    components.innerHTML = `
        <div>
            <span>Aluguel</span>
            <strong>#${summary.aluguel.id}</strong>
            <small>${escapeHtml(summary.aluguel.cliente_nome)}</small>
        </div>
        <div>
            <span>Devolução registrada</span>
            <strong>${formatCurrency(summary.valor_devolucao)}</strong>
            <small>Inclui a liquidação legada da devolução quando existente.</small>
        </div>
        <div>
            <span>Danos ativos</span>
            <strong>${formatCurrency(summary.danos_total)}</strong>
            <small>Fonte: vistoria</small>
        </div>
        <div>
            <span>Multas de trânsito</span>
            <strong>${formatCurrency(summary.multas_transito_total)}</strong>
            <small>Fonte: vistoria</small>
        </div>
    `;

    paymentValue.max = String(
        summary.saldo_pendente
    );
    paymentValue.value = (
        summary.saldo_pendente > 0
            ? String(summary.saldo_pendente)
            : ""
    );
    paymentForm.hidden = (
        !can(Permissions.FINANCEIRO_RECEBER)
        || summary.saldo_pendente <= 0
    );

    renderPayments();
}

async function loadAccounts() {
    refreshButton.disabled = true;

    try {
        const data = await getFinancialAccounts(
            page,
            12,
            searchInput.value.trim(),
        );
        renderAccounts(data);
    } catch (error) {
        if (
            error instanceof ApiError
            && error.status === 401
        ) {
            clearToken();
            goToLogin();
            return;
        }
        showMessage(error.message);
    } finally {
        refreshButton.disabled = false;
    }
}

async function loadSummary() {
    if (!selectedRentalId) {
        return;
    }

    clearMessage();

    try {
        summary = await getRentalFinancialSummary(
            selectedRentalId
        );
        renderSummary();
    } catch (error) {
        showMessage(error.message);
    }
}

paymentMethod.addEventListener("change", () => {
    if (paymentMethod.value !== "credito") {
        paymentInstallments.value = "1";
        paymentInstallments.disabled = true;
    } else {
        paymentInstallments.disabled = false;
    }
});

paymentForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    if (!selectedRentalId) {
        return;
    }

    try {
        await createFinancialPayment(
            selectedRentalId,
            {
                valor: Number(paymentValue.value),
                forma: paymentMethod.value,
                parcelas: Number(paymentInstallments.value),
                observacoes: paymentNotes.value.trim() || null,
            },
        );
        paymentNotes.value = "";
        await loadSummary();
        await loadAccounts();
        showMessage(
            "Pagamento registrado.",
            "success",
        );
    } catch (error) {
        showMessage(error.message);
    }
});

refreshButton.addEventListener("click", () => loadAccounts());

prevButton.addEventListener("click", () => {
    if (page > 1) {
        page -= 1;
        loadAccounts();
    }
});

nextButton.addEventListener("click", () => {
    if (page < totalPages) {
        page += 1;
        loadAccounts();
    }
});

searchInput.addEventListener("input", () => {
    window.clearTimeout(searchTimer);
    searchTimer = window.setTimeout(() => {
        page = 1;
        loadAccounts();
    }, 300);
});

logoutButton.addEventListener("click", async () => {
    try {
        await logout();
    } finally {
        goToLogin();
    }
});

async function initialize() {
    if (!(await restoreSession())) {
        goToLogin();
        return;
    }

    try {
        currentUser = await getCurrentUser();
        applyNavigationPermissions(currentUser);
        roleBadge.textContent = currentUser.role;

        if (!can(Permissions.FINANCEIRO_LER)) {
            window.location.replace(
                "/app/dashboard.html"
            );
            return;
        }

        paymentInstallments.disabled = true;
        await loadAccounts();
    } catch (error) {
        showMessage(
            error.message
            ?? "Não foi possível preparar a página."
        );
    }
}

initialize();
