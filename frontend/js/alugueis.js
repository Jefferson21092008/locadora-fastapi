import {
    ApiError,
    clearToken,
    createRental,
    getCurrentUser,
    getMyRentals,
    getRentals,
    getToken,
    getVehicles,
    returnVehicle,
} from "/app/js/api.js";

const roleBadge = document.querySelector("#current-role");
const logoutButton = document.querySelector("#logout-button");
const newRentalButton = document.querySelector("#new-rental-button");
const refreshButton = document.querySelector("#refresh-rentals-button");
const searchInput = document.querySelector("#rental-search");
const statusFilter = document.querySelector("#rental-status-filter");
const pageMessage = document.querySelector("#rentals-message");
const loadingState = document.querySelector("#rentals-loading");
const emptyState = document.querySelector("#rentals-empty");
const emptyText = document.querySelector("#rentals-empty-text");
const rentalsList = document.querySelector("#rentals-list");
const rentalsEyebrow = document.querySelector("#rentals-eyebrow");
const rentalsDescription = document.querySelector("#rentals-description");
const rentalsListTitle = document.querySelector("#rentals-list-title");

const rentalDialog = document.querySelector("#rental-dialog");
const rentalForm = document.querySelector("#rental-form");
const rentalVehicleInput = document.querySelector("#rental-vehicle");
const rentalDaysInput = document.querySelector("#rental-days");
const licenseYearsField = document.querySelector("#license-years-field");
const licenseYearsInput = document.querySelector("#license-years");
const rentalEstimate = document.querySelector("#rental-estimate");
const rentalDailyRate = document.querySelector("#rental-daily-rate");
const rentalEstimatedTotal = document.querySelector("#rental-estimated-total");
const rentalFormMessage = document.querySelector("#rental-form-message");
const saveRentalButton = document.querySelector("#save-rental-button");

const returnDialog = document.querySelector("#return-dialog");
const returnForm = document.querySelector("#return-form");
const returnDialogTitle = document.querySelector("#return-dialog-title");
const returnDialogDescription = document.querySelector("#return-dialog-description");
const returnVehicleIdInput = document.querySelector("#return-vehicle-id");
const returnDistanceInput = document.querySelector("#return-distance");
const paymentMethodInput = document.querySelector("#payment-method");
const installmentsField = document.querySelector("#installments-field");
const paymentInstallmentsInput = document.querySelector("#payment-installments");
const returnFormMessage = document.querySelector("#return-form-message");
const confirmReturnButton = document.querySelector("#confirm-return-button");

const summaryElements = {
    total: document.querySelector("#rentals-summary-total"),
    active: document.querySelector("#rentals-summary-active"),
    finished: document.querySelector("#rentals-summary-finished"),
    late: document.querySelector("#rentals-summary-late"),
};

let currentUser = null;
let rentals = [];
let vehicles = [];

function goToLogin() {
    window.location.replace("/app/");
}

function isAdmin() {
    return currentUser?.role === "admin";
}

function normalizeText(value) {
    return String(value ?? "")
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .trim()
        .toLowerCase();
}

function escapeHtml(value) {
    const characters = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;",
    };

    return String(value ?? "").replace(/[&<>"']/g, (character) => characters[character]);
}

function formatCurrency(value) {
    return Number(value ?? 0).toLocaleString("pt-BR", {
        style: "currency",
        currency: "BRL",
    });
}

function formatNumber(value) {
    return Number(value ?? 0).toLocaleString("pt-BR", {
        maximumFractionDigits: 1,
    });
}

function formatDate(value) {
    if (!value) {
        return "—";
    }

    const parsedDate = new Date(`${value}T00:00:00`);

    if (Number.isNaN(parsedDate.getTime())) {
        return value;
    }

    return parsedDate.toLocaleDateString("pt-BR");
}

function todayIsoDate() {
    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, "0");
    const day = String(today.getDate()).padStart(2, "0");

    return `${year}-${month}-${day}`;
}

function isLate(rental) {
    return rental.status === "ativo" && rental.data_prevista < todayIsoDate();
}

function showMessage(element, text, type = "error") {
    element.textContent = text;
    element.classList.add("form-message--visible", `form-message--${type}`);
}

function clearMessage(element) {
    element.textContent = "";
    element.classList.remove(
        "form-message--visible",
        "form-message--error",
        "form-message--success",
    );
}

function configureCurrentUser(user) {
    currentUser = user;
    roleBadge.textContent = isAdmin() ? "Administrador" : "Cliente";
    newRentalButton.hidden = isAdmin();
    for (const link of document.querySelectorAll(".admin-nav")) {
        link.hidden = !isAdmin();
    }

    if (isAdmin()) {
        rentalsEyebrow.textContent = "Operação";
        rentalsDescription.textContent = "Acompanhe todos os contratos e prazos da locadora.";
        rentalsListTitle.textContent = "Todos os aluguéis";
    }
}

function updateSummary() {
    const counts = {
        total: rentals.length,
        active: rentals.filter((rental) => rental.status === "ativo").length,
        finished: rentals.filter((rental) => rental.status === "finalizado").length,
        late: rentals.filter(isLate).length,
    };

    for (const [name, element] of Object.entries(summaryElements)) {
        element.textContent = counts[name].toLocaleString("pt-BR");
    }
}

function filteredRentals() {
    const query = normalizeText(searchInput.value);
    const selectedStatus = statusFilter.value;

    return rentals.filter((rental) => {
        const matchesStatus = selectedStatus === "todos" || rental.status === selectedStatus;
        const searchableText = normalizeText([
            rental.id,
            rental.veiculo_id,
            rental.veiculo_tipo,
            rental.veiculo_modelo,
            rental.cliente_id,
            rental.cliente_nome,
            rental.cliente_usuario,
        ].join(" "));

        return matchesStatus && searchableText.includes(query);
    });
}

function rentalFinancialDetails(rental) {
    if (rental.status === "ativo") {
        return `
            <div>
                <dt>Prazo contratado</dt>
                <dd>${rental.dias} ${rental.dias === 1 ? "dia" : "dias"}</dd>
            </div>
            <div>
                <dt>Situação</dt>
                <dd>${isLate(rental) ? "Prazo vencido" : "Em andamento"}</dd>
            </div>
        `;
    }

    return `
        <div>
            <dt>Valor pago</dt>
            <dd>${formatCurrency(rental.valor)}</dd>
        </div>
        <div>
            <dt>Pagamento</dt>
            <dd>${escapeHtml(rental.pagamento ?? "Não informado")}</dd>
        </div>
        <div>
            <dt>Quilometragem</dt>
            <dd>${formatNumber(rental.km)} km</dd>
        </div>
        <div>
            <dt>Multa</dt>
            <dd>${formatCurrency(rental.multa)}</dd>
        </div>
    `;
}

function rentalCustomer(rental) {
    if (!isAdmin()) {
        return "";
    }

    return `
        <div class="rental-card__customer">
            <span>Cliente</span>
            <strong>${escapeHtml(rental.cliente_nome)}</strong>
            <small>@${escapeHtml(rental.cliente_usuario)} · ID ${rental.cliente_id}</small>
        </div>
    `;
}

function rentalAction(rental) {
    if (isAdmin() || rental.status !== "ativo") {
        return "";
    }

    return `
        <button class="card-button card-button--success" type="button" data-action="return" data-id="${rental.id}">
            Devolver veículo
        </button>
    `;
}

function renderRentals() {
    const results = filteredRentals();
    emptyState.hidden = results.length > 0;

    if (results.length === 0) {
        emptyText.textContent = rentals.length === 0
            ? (isAdmin()
                ? "Ainda não há aluguéis registrados na locadora."
                : "Você ainda não possui aluguéis. Use “Novo aluguel” para começar.")
            : "Altere a busca ou o filtro para visualizar outros resultados.";
    }

    rentalsList.innerHTML = results.map((rental) => {
        const late = isLate(rental);
        const statusLabel = rental.status === "ativo" ? "Ativo" : "Finalizado";
        const actionHtml = rentalAction(rental);

        return `
            <article class="rental-card ${late ? "rental-card--late" : ""}">
                <div class="rental-card__main">
                    <div class="rental-card__header">
                        <span class="rental-card__id">Aluguel #${rental.id}</span>
                        <span class="rental-status rental-status--${escapeHtml(rental.status)}">
                            ${late ? "Prazo vencido" : statusLabel}
                        </span>
                    </div>

                    <div class="rental-card__vehicle">
                        <span>${escapeHtml(rental.veiculo_tipo)} · veículo #${rental.veiculo_id}</span>
                        <h3>${escapeHtml(rental.veiculo_modelo)}</h3>
                    </div>

                    ${rentalCustomer(rental)}
                </div>

                <dl class="rental-card__dates">
                    <div>
                        <dt>Retirada</dt>
                        <dd>${formatDate(rental.data_inicio)}</dd>
                    </div>
                    <div>
                        <dt>Previsão</dt>
                        <dd>${formatDate(rental.data_prevista)}</dd>
                    </div>
                    <div>
                        <dt>Devolução</dt>
                        <dd>${formatDate(rental.data_fim)}</dd>
                    </div>
                </dl>

                <dl class="rental-card__financial">
                    ${rentalFinancialDetails(rental)}
                </dl>

                ${actionHtml ? `<div class="rental-card__actions">${actionHtml}</div>` : ""}
            </article>
        `;
    }).join("");

    for (const button of rentalsList.querySelectorAll('[data-action="return"]')) {
        button.addEventListener("click", handleReturnAction);
    }
}

function availableVehicles() {
    return vehicles
        .filter((vehicle) => vehicle.status === "disponivel")
        .sort((first, second) => first.modelo.localeCompare(second.modelo, "pt-BR"));
}

function populateVehicleOptions() {
    const available = availableVehicles();
    const options = available.map((vehicle) => `
        <option value="${vehicle.id}">
            ${escapeHtml(vehicle.modelo)} · ${escapeHtml(vehicle.tipo)} · ${formatCurrency(vehicle.diaria)}/dia
        </option>
    `).join("");

    rentalVehicleInput.innerHTML = `
        <option value="">${available.length > 0 ? "Selecione um veículo" : "Nenhum veículo disponível"}</option>
        ${options}
    `;
    saveRentalButton.disabled = available.length === 0;
}

function selectedVehicle() {
    return vehicles.find((vehicle) => vehicle.id === Number(rentalVehicleInput.value));
}

function updateRentalEstimate() {
    const vehicle = selectedVehicle();

    if (!vehicle) {
        rentalEstimate.hidden = true;
        licenseYearsField.hidden = false;
        licenseYearsInput.required = true;
        return;
    }

    const days = Math.max(Number(rentalDaysInput.value) || 0, 0);
    const requiresLicense = normalizeText(vehicle.tipo) !== "bicicleta";

    licenseYearsField.hidden = !requiresLicense;
    licenseYearsInput.required = requiresLicense;
    if (!requiresLicense) {
        licenseYearsInput.value = "";
    }

    rentalDailyRate.textContent = formatCurrency(vehicle.diaria);
    rentalEstimatedTotal.textContent = formatCurrency(vehicle.diaria * days);
    rentalEstimate.hidden = false;
}

function openRentalDialog() {
    rentalForm.reset();
    clearMessage(rentalFormMessage);
    populateVehicleOptions();
    rentalDaysInput.value = "1";
    rentalEstimate.hidden = true;
    licenseYearsField.hidden = false;
    licenseYearsInput.required = true;
    rentalDialog.showModal();
    rentalVehicleInput.focus();
}

function closeRentalDialog() {
    if (!saveRentalButton.disabled || availableVehicles().length === 0) {
        rentalDialog.close();
    }
}

async function saveRental(event) {
    event.preventDefault();
    clearMessage(rentalFormMessage);

    if (!rentalForm.reportValidity()) {
        return;
    }

    const vehicle = selectedVehicle();
    if (!vehicle) {
        showMessage(rentalFormMessage, "Selecione um veículo disponível.");
        return;
    }

    const payload = {
        id_veiculo: vehicle.id,
        dias: Number(rentalDaysInput.value),
        anos_habilitacao: normalizeText(vehicle.tipo) === "bicicleta"
            ? null
            : Number(licenseYearsInput.value),
    };

    saveRentalButton.disabled = true;
    saveRentalButton.querySelector("span:first-child").textContent = "Confirmando...";

    try {
        await createRental(payload);
        rentalDialog.close();
        showMessage(pageMessage, "Aluguel criado com sucesso.", "success");
        await loadRentals({ preserveMessage: true });
    } catch (error) {
        if (error instanceof ApiError && error.status === 401) {
            clearToken();
            goToLogin();
            return;
        }

        showMessage(rentalFormMessage, error.message);
    } finally {
        saveRentalButton.disabled = false;
        saveRentalButton.querySelector("span:first-child").textContent = "Confirmar aluguel";
    }
}

function findRental(rentalId) {
    return rentals.find((rental) => rental.id === Number(rentalId));
}

function handleReturnAction(event) {
    const rental = findRental(event.currentTarget.dataset.id);
    if (!rental) {
        return;
    }

    returnForm.reset();
    clearMessage(returnFormMessage);
    returnVehicleIdInput.value = String(rental.veiculo_id);
    returnDialogTitle.textContent = `Devolver ${rental.veiculo_modelo}`;
    returnDialogDescription.textContent = `Informe a distância percorrida no aluguel #${rental.id}. O valor final será calculado pela API.`;
    updatePaymentFields();
    returnDialog.showModal();
    returnDistanceInput.focus();
}

function updatePaymentFields() {
    const isInstallmentPayment = paymentMethodInput.value === "5";
    installmentsField.hidden = !isInstallmentPayment;
    paymentInstallmentsInput.required = isInstallmentPayment;
}

function closeReturnDialog() {
    if (!confirmReturnButton.disabled) {
        returnDialog.close();
    }
}

async function submitReturn(event) {
    event.preventDefault();
    clearMessage(returnFormMessage);

    if (!returnForm.reportValidity()) {
        return;
    }

    const paymentMethod = Number(paymentMethodInput.value);
    const payload = {
        km: Number(returnDistanceInput.value),
        forma_pagamento: paymentMethod,
        parcelas: paymentMethod === 5 ? Number(paymentInstallmentsInput.value) : null,
    };

    confirmReturnButton.disabled = true;
    confirmReturnButton.querySelector("span:first-child").textContent = "Processando...";

    try {
        const result = await returnVehicle(returnVehicleIdInput.value, payload);
        const installmentText = result.pagamento.parcelas > 1
            ? ` em ${result.pagamento.parcelas}x de ${formatCurrency(result.pagamento.valor_parcela)}`
            : "";

        returnDialog.close();
        showMessage(
            pageMessage,
            `Devolução concluída: ${formatCurrency(result.pagamento.valor_final)} via ${result.pagamento.forma}${installmentText}.`,
            "success",
        );
        await loadRentals({ preserveMessage: true });
    } catch (error) {
        if (error instanceof ApiError && error.status === 401) {
            clearToken();
            goToLogin();
            return;
        }

        showMessage(returnFormMessage, error.message);
    } finally {
        confirmReturnButton.disabled = false;
        confirmReturnButton.querySelector("span:first-child").textContent = "Concluir devolução";
    }
}

async function loadRentals({ preserveMessage = false } = {}) {
    if (!preserveMessage) {
        clearMessage(pageMessage);
    }

    loadingState.hidden = false;
    emptyState.hidden = true;
    rentalsList.setAttribute("aria-busy", "true");
    refreshButton.disabled = true;

    try {
        if (isAdmin()) {
            rentals = await getRentals();
        } else {
            [rentals, vehicles] = await Promise.all([
                getMyRentals(),
                getVehicles(),
            ]);
        }

        updateSummary();
        renderRentals();
    } catch (error) {
        if (error instanceof ApiError && error.status === 401) {
            clearToken();
            goToLogin();
            return;
        }

        showMessage(pageMessage, error.message);
    } finally {
        loadingState.hidden = true;
        rentalsList.removeAttribute("aria-busy");
        refreshButton.disabled = false;
    }
}

async function initialize() {
    if (!getToken()) {
        goToLogin();
        return;
    }

    try {
        configureCurrentUser(await getCurrentUser());
        await loadRentals();
    } catch (error) {
        if (error instanceof ApiError && error.status === 401) {
            clearToken();
            goToLogin();
            return;
        }

        loadingState.hidden = true;
        showMessage(pageMessage, error.message);
    }
}

logoutButton.addEventListener("click", () => {
    clearToken();
    goToLogin();
});

newRentalButton.addEventListener("click", openRentalDialog);
refreshButton.addEventListener("click", () => loadRentals());
searchInput.addEventListener("input", renderRentals);
statusFilter.addEventListener("change", renderRentals);
rentalVehicleInput.addEventListener("change", updateRentalEstimate);
rentalDaysInput.addEventListener("input", updateRentalEstimate);
rentalForm.addEventListener("submit", saveRental);
paymentMethodInput.addEventListener("change", updatePaymentFields);
returnForm.addEventListener("submit", submitReturn);

for (const button of document.querySelectorAll("[data-close-rental-dialog]")) {
    button.addEventListener("click", closeRentalDialog);
}

for (const button of document.querySelectorAll("[data-close-return-dialog]")) {
    button.addEventListener("click", closeReturnDialog);
}

initialize();
