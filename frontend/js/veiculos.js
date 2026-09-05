import {
    ApiError,
    clearToken,
    createVehicle,
    deactivateVehicle,
    getCurrentUser,
    getToken,
    getVehicles,
    reactivateVehicle,
    updateVehicle,
} from "/app/js/api.js";

const roleBadge = document.querySelector("#current-role");
const logoutButton = document.querySelector("#logout-button");
const newVehicleButton = document.querySelector("#new-vehicle-button");
const refreshButton = document.querySelector("#refresh-vehicles-button");
const searchInput = document.querySelector("#vehicle-search");
const statusFilter = document.querySelector("#status-filter");
const pageMessage = document.querySelector("#vehicles-message");
const loadingState = document.querySelector("#vehicles-loading");
const emptyState = document.querySelector("#vehicles-empty");
const vehiclesGrid = document.querySelector("#vehicles-grid");

const vehicleDialog = document.querySelector("#vehicle-dialog");
const vehicleForm = document.querySelector("#vehicle-form");
const vehicleDialogEyebrow = document.querySelector("#vehicle-dialog-eyebrow");
const vehicleDialogTitle = document.querySelector("#vehicle-dialog-title");
const vehicleIdInput = document.querySelector("#vehicle-id");
const vehicleTypeInput = document.querySelector("#vehicle-type");
const vehicleModelInput = document.querySelector("#vehicle-model");
const vehicleYearInput = document.querySelector("#vehicle-year");
const vehicleDailyRateInput = document.querySelector("#vehicle-daily-rate");
const vehicleKmRateInput = document.querySelector("#vehicle-km-rate");
const vehicleFormMessage = document.querySelector("#vehicle-form-message");
const saveVehicleButton = document.querySelector("#save-vehicle-button");

const statusDialog = document.querySelector("#status-dialog");
const statusDialogTitle = document.querySelector("#status-dialog-title");
const statusDialogText = document.querySelector("#status-dialog-text");
const statusFormMessage = document.querySelector("#status-form-message");
const confirmStatusButton = document.querySelector("#confirm-status-button");

const summaryElements = {
    total: document.querySelector("#summary-total"),
    disponivel: document.querySelector("#summary-disponivel"),
    alugado: document.querySelector("#summary-alugado"),
    manutencao: document.querySelector("#summary-manutencao"),
    desativado: document.querySelector("#summary-desativado"),
};

const statusLabels = {
    disponivel: "Disponível",
    alugado: "Alugado",
    manutencao: "Em manutenção",
    desativado: "Desativado",
};

let currentUser = null;
let vehicles = [];
let pendingStatusAction = null;

function goToLogin() {
    window.location.replace("/app/");
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

function formatDistance(value) {
    return `${Number(value ?? 0).toLocaleString("pt-BR", {
        maximumFractionDigits: 1,
    })} km`;
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

function isAdmin() {
    return currentUser?.role === "admin";
}

function updateSummary() {
    const counts = {
        total: vehicles.length,
        disponivel: 0,
        alugado: 0,
        manutencao: 0,
        desativado: 0,
    };

    for (const vehicle of vehicles) {
        if (Object.hasOwn(counts, vehicle.status)) {
            counts[vehicle.status] += 1;
        }
    }

    for (const [name, element] of Object.entries(summaryElements)) {
        element.textContent = counts[name].toLocaleString("pt-BR");
    }
}

function filteredVehicles() {
    const query = normalizeText(searchInput.value);
    const selectedStatus = statusFilter.value;

    return vehicles.filter((vehicle) => {
        const matchesStatus = selectedStatus === "todos" || vehicle.status === selectedStatus;
        const searchableText = normalizeText(
            `${vehicle.id} ${vehicle.tipo} ${vehicle.modelo} ${vehicle.ano}`,
        );

        return matchesStatus && searchableText.includes(query);
    });
}

function adminActions(vehicle) {
    if (!isAdmin()) {
        return "";
    }

    if (vehicle.status === "desativado") {
        return `
            <button class="card-button card-button--success" type="button" data-action="reactivate" data-id="${vehicle.id}">
                Reativar
            </button>
        `;
    }

    if (vehicle.status !== "disponivel") {
        return `
            <span class="vehicle-card__locked">Alterações bloqueadas neste status</span>
        `;
    }

    return `
        <button class="card-button" type="button" data-action="edit" data-id="${vehicle.id}">
            Editar
        </button>
        <button class="card-button card-button--danger" type="button" data-action="deactivate" data-id="${vehicle.id}">
            Desativar
        </button>
    `;
}

function renderVehicles() {
    const results = filteredVehicles();
    emptyState.hidden = results.length > 0;

    vehiclesGrid.innerHTML = results.map((vehicle) => `
        <article class="vehicle-card vehicle-card--${escapeHtml(vehicle.status)}">
            <div class="vehicle-card__topline">
                <span class="vehicle-type">${escapeHtml(vehicle.tipo)}</span>
                <span class="status-badge status-badge--${escapeHtml(vehicle.status)}">
                    ${escapeHtml(statusLabels[vehicle.status] ?? vehicle.status)}
                </span>
            </div>

            <div class="vehicle-card__identity">
                <h3>${escapeHtml(vehicle.modelo)}</h3>
                <p>ID ${vehicle.id} · ${vehicle.ano}</p>
            </div>

            <dl class="vehicle-card__details">
                <div>
                    <dt>Diária</dt>
                    <dd>${formatCurrency(vehicle.diaria)}</dd>
                </div>
                <div>
                    <dt>Preço por km</dt>
                    <dd>${formatCurrency(vehicle.preco_km)}</dd>
                </div>
                <div>
                    <dt>Quilometragem</dt>
                    <dd>${formatDistance(vehicle.quilometragem)}</dd>
                </div>
            </dl>

            ${isAdmin() ? `<div class="vehicle-card__actions">${adminActions(vehicle)}</div>` : ""}
        </article>
    `).join("");

    for (const button of vehiclesGrid.querySelectorAll("[data-action]")) {
        button.addEventListener("click", handleVehicleAction);
    }
}

function findVehicle(vehicleId) {
    return vehicles.find((vehicle) => vehicle.id === Number(vehicleId));
}

function handleVehicleAction(event) {
    const vehicle = findVehicle(event.currentTarget.dataset.id);
    if (!vehicle) {
        return;
    }

    const action = event.currentTarget.dataset.action;

    if (action === "edit") {
        openEditDialog(vehicle);
        return;
    }

    openStatusDialog(vehicle, action);
}

function configureCurrentUser(user) {
    currentUser = user;
    roleBadge.textContent = user.role === "admin" ? "Administrador" : "Cliente";
    newVehicleButton.hidden = !isAdmin();
    for (const link of document.querySelectorAll(".admin-nav")) {
        link.hidden = !isAdmin();
    }
}

async function loadVehicles({ preserveMessage = false } = {}) {
    if (!preserveMessage) {
        clearMessage(pageMessage);
    }

    loadingState.hidden = false;
    emptyState.hidden = true;
    vehiclesGrid.setAttribute("aria-busy", "true");
    refreshButton.disabled = true;

    try {
        vehicles = await getVehicles();
        updateSummary();
        renderVehicles();
    } catch (error) {
        if (error instanceof ApiError && error.status === 401) {
            clearToken();
            goToLogin();
            return;
        }

        showMessage(pageMessage, error.message);
    } finally {
        loadingState.hidden = true;
        vehiclesGrid.removeAttribute("aria-busy");
        refreshButton.disabled = false;
    }
}

function openCreateDialog() {
    vehicleForm.reset();
    clearMessage(vehicleFormMessage);
    vehicleIdInput.value = "";
    vehicleTypeInput.disabled = false;
    vehicleYearInput.max = String(new Date().getFullYear() + 1);
    vehicleYearInput.value = String(new Date().getFullYear());
    vehicleDialogEyebrow.textContent = "Cadastro";
    vehicleDialogTitle.textContent = "Novo veículo";
    saveVehicleButton.querySelector("span:first-child").textContent = "Cadastrar veículo";
    vehicleDialog.showModal();
    vehicleModelInput.focus();
}

function openEditDialog(vehicle) {
    vehicleForm.reset();
    clearMessage(vehicleFormMessage);
    vehicleIdInput.value = String(vehicle.id);
    vehicleTypeInput.value = normalizeText(vehicle.tipo);
    vehicleTypeInput.disabled = true;
    vehicleModelInput.value = vehicle.modelo;
    vehicleYearInput.value = String(vehicle.ano);
    vehicleYearInput.max = String(new Date().getFullYear() + 1);
    vehicleDailyRateInput.value = String(vehicle.diaria);
    vehicleKmRateInput.value = String(vehicle.preco_km);
    vehicleDialogEyebrow.textContent = `Veículo #${vehicle.id}`;
    vehicleDialogTitle.textContent = "Editar veículo";
    saveVehicleButton.querySelector("span:first-child").textContent = "Salvar alterações";
    vehicleDialog.showModal();
    vehicleModelInput.focus();
}

function closeVehicleDialog() {
    if (!saveVehicleButton.disabled) {
        vehicleDialog.close();
    }
}

function vehiclePayload() {
    return {
        modelo: vehicleModelInput.value.trim(),
        ano: Number(vehicleYearInput.value),
        diaria: Number(vehicleDailyRateInput.value),
        preco_km: Number(vehicleKmRateInput.value),
    };
}

async function saveVehicle(event) {
    event.preventDefault();
    clearMessage(vehicleFormMessage);

    if (!vehicleForm.reportValidity()) {
        return;
    }

    const vehicleId = vehicleIdInput.value;
    const editing = Boolean(vehicleId);
    const payload = vehiclePayload();

    if (!editing) {
        payload.tipo = vehicleTypeInput.value;
    }

    saveVehicleButton.disabled = true;
    saveVehicleButton.querySelector("span:first-child").textContent = editing
        ? "Salvando..."
        : "Cadastrando...";

    try {
        if (editing) {
            await updateVehicle(vehicleId, payload);
        } else {
            await createVehicle(payload);
        }

        vehicleDialog.close();
        showMessage(
            pageMessage,
            editing ? "Veículo atualizado com sucesso." : "Veículo cadastrado com sucesso.",
            "success",
        );
        await loadVehicles({ preserveMessage: true });
    } catch (error) {
        if (error instanceof ApiError && error.status === 401) {
            clearToken();
            goToLogin();
            return;
        }

        showMessage(vehicleFormMessage, error.message);
    } finally {
        saveVehicleButton.disabled = false;
        saveVehicleButton.querySelector("span:first-child").textContent = editing
            ? "Salvar alterações"
            : "Cadastrar veículo";
    }
}

function openStatusDialog(vehicle, action) {
    pendingStatusAction = { vehicle, action };
    clearMessage(statusFormMessage);

    const reactivating = action === "reactivate";
    statusDialogTitle.textContent = reactivating ? "Reativar veículo" : "Desativar veículo";
    statusDialogText.textContent = reactivating
        ? `O veículo ${vehicle.modelo} voltará a ficar disponível na frota.`
        : `O veículo ${vehicle.modelo} ficará indisponível para novos aluguéis.`;
    confirmStatusButton.querySelector("span:first-child").textContent = reactivating
        ? "Reativar"
        : "Desativar";
    statusDialog.showModal();
    confirmStatusButton.focus();
}

function closeStatusDialog() {
    if (!confirmStatusButton.disabled) {
        pendingStatusAction = null;
        statusDialog.close();
    }
}

async function confirmStatusChange() {
    if (!pendingStatusAction) {
        return;
    }

    clearMessage(statusFormMessage);
    confirmStatusButton.disabled = true;
    const { vehicle, action } = pendingStatusAction;
    const reactivating = action === "reactivate";

    try {
        if (reactivating) {
            await reactivateVehicle(vehicle.id);
        } else {
            await deactivateVehicle(vehicle.id);
        }

        statusDialog.close();
        pendingStatusAction = null;
        showMessage(
            pageMessage,
            reactivating ? "Veículo reativado com sucesso." : "Veículo desativado com sucesso.",
            "success",
        );
        await loadVehicles({ preserveMessage: true });
    } catch (error) {
        if (error instanceof ApiError && error.status === 401) {
            clearToken();
            goToLogin();
            return;
        }

        showMessage(statusFormMessage, error.message);
    } finally {
        confirmStatusButton.disabled = false;
    }
}

async function initialize() {
    if (!getToken()) {
        goToLogin();
        return;
    }

    try {
        configureCurrentUser(await getCurrentUser());
        await loadVehicles();
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

newVehicleButton.addEventListener("click", openCreateDialog);
refreshButton.addEventListener("click", () => loadVehicles());
searchInput.addEventListener("input", renderVehicles);
statusFilter.addEventListener("change", renderVehicles);
vehicleForm.addEventListener("submit", saveVehicle);
confirmStatusButton.addEventListener("click", confirmStatusChange);

for (const button of document.querySelectorAll("[data-close-vehicle-dialog]")) {
    button.addEventListener("click", closeVehicleDialog);
}

for (const button of document.querySelectorAll("[data-close-status-dialog]")) {
    button.addEventListener("click", closeStatusDialog);
}

initialize();
