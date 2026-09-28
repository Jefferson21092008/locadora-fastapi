import {
    ApiError,
    Permissions,
    applyNavigationPermissions,
    clearToken,
    createVehicle,
    deactivateVehicle,
    getCurrentUser,
    restoreSession,
    hasPermission,
    logout,
    queryVehicles,
    reactivateVehicle,
    updateVehicle,
} from "/app/js/api.js";

const roleBadge = document.querySelector("#current-role");
const logoutButton = document.querySelector("#logout-button");
const newVehicleButton = document.querySelector("#new-vehicle-button");
const refreshButton = document.querySelector("#refresh-vehicles-button");
const searchInput = document.querySelector("#vehicle-search");
const statusFilter = document.querySelector("#status-filter");
const orderSelect = document.querySelector("#vehicle-order");
const pageSizeSelect = document.querySelector("#vehicle-page-size");
const previousPageButton = document.querySelector("#vehicles-page-previous");
const nextPageButton = document.querySelector("#vehicles-page-next");
const pageLabel = document.querySelector("#vehicles-page-label");
const resultsCount = document.querySelector("#vehicles-results-count");
const clearFiltersButton = document.querySelector("#clear-vehicle-filters");
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
let searchTimer = null;
let pagination = { pagina: 1, total: 0, total_paginas: 0 };
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

function can(permission) {
    return hasPermission(currentUser, permission);
}

function updateSummary(resumo) {
    const counts = {
        total: resumo.total,
        disponivel: resumo.disponiveis,
        alugado: resumo.alugados,
        manutencao: resumo.manutencao,
        desativado: resumo.desativados,
    };

    for (const [name, element] of Object.entries(summaryElements)) {
        element.textContent = Number(counts[name] ?? 0).toLocaleString("pt-BR");
    }
}

function updatePagination() {
    const current = pagination.total_paginas === 0 ? 0 : pagination.pagina;
    pageLabel.textContent = `Página ${current} de ${pagination.total_paginas}`;
    previousPageButton.disabled = pagination.pagina <= 1;
    nextPageButton.disabled = pagination.pagina >= pagination.total_paginas;
}

function orderParams() {
    const [ordenar, direcao] = orderSelect.value.split(":");
    return { ordenar, direcao };
}

function filteredVehicles() {
    return vehicles;
}

function vehicleActions(vehicle) {
    if (vehicle.status === "desativado") {
        return can(Permissions.VEICULOS_GERENCIAR_STATUS)
            ? `
                <button class="card-button card-button--success" type="button" data-action="reactivate" data-id="${vehicle.id}">
                    Reativar
                </button>
            `
            : "";
    }

    if (vehicle.status !== "disponivel") {
        const canChange = can(Permissions.VEICULOS_EDITAR)
            || can(Permissions.VEICULOS_GERENCIAR_STATUS);
        return canChange
            ? '<span class="vehicle-card__locked">Alterações bloqueadas neste status</span>'
            : "";
    }

    const actions = [];

    if (can(Permissions.VEICULOS_EDITAR)) {
        actions.push(`
            <button class="card-button" type="button" data-action="edit" data-id="${vehicle.id}">
                Editar
            </button>
        `);
    }

    if (can(Permissions.VEICULOS_GERENCIAR_STATUS)) {
        actions.push(`
            <button class="card-button card-button--danger" type="button" data-action="deactivate" data-id="${vehicle.id}">
                Desativar
            </button>
        `);
    }

    return actions.join("");
}

function renderVehicles() {
    const results = filteredVehicles();
    const hasActiveFilters = Boolean(normalizeText(searchInput.value))
        || statusFilter.value !== "todos";

    resultsCount.textContent = `${results.length.toLocaleString("pt-BR")} nesta página · ${pagination.total.toLocaleString("pt-BR")} resultados`;
    clearFiltersButton.hidden = !hasActiveFilters;

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

            ${vehicleActions(vehicle) ? `<div class="vehicle-card__actions">${vehicleActions(vehicle)}</div>` : ""}
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
    newVehicleButton.hidden = !can(Permissions.VEICULOS_CRIAR);
    applyNavigationPermissions(user);
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
        const result = await queryVehicles({
            pagina: pagination.pagina,
            por_pagina: Number(pageSizeSelect.value),
            busca: searchInput.value.trim(),
            status: statusFilter.value,
            ...orderParams(),
        });
        if (result.total_paginas > 0 && pagination.pagina > result.total_paginas) {
            pagination.pagina = result.total_paginas;
            return loadVehicles({ preserveMessage: true });
        }

        vehicles = result.items;
        pagination = {
            pagina: result.pagina,
            total: result.total,
            total_paginas: result.total_paginas,
        };
        updateSummary(result.resumo);
        updatePagination();
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
    if (!(await restoreSession())) {
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

logoutButton.addEventListener("click", async () => {
    await logout();
    goToLogin();
});

newVehicleButton.addEventListener("click", openCreateDialog);
refreshButton.addEventListener("click", () => loadVehicles());
searchInput.addEventListener("input", () => {
    window.clearTimeout(searchTimer);
    searchTimer = window.setTimeout(() => {
        pagination.pagina = 1;
        loadVehicles();
    }, 300);
});
statusFilter.addEventListener("change", () => {
    pagination.pagina = 1;
    loadVehicles();
});
orderSelect.addEventListener("change", () => {
    pagination.pagina = 1;
    loadVehicles();
});
pageSizeSelect.addEventListener("change", () => {
    pagination.pagina = 1;
    loadVehicles();
});
previousPageButton.addEventListener("click", () => {
    if (pagination.pagina > 1) {
        pagination.pagina -= 1;
        loadVehicles();
    }
});
nextPageButton.addEventListener("click", () => {
    if (pagination.pagina < pagination.total_paginas) {
        pagination.pagina += 1;
        loadVehicles();
    }
});
clearFiltersButton.addEventListener("click", () => {
    searchInput.value = "";
    statusFilter.value = "todos";
    pagination.pagina = 1;
    loadVehicles();
    searchInput.focus();
});
vehicleForm.addEventListener("submit", saveVehicle);
confirmStatusButton.addEventListener("click", confirmStatusChange);

for (const button of document.querySelectorAll("[data-close-vehicle-dialog]")) {
    button.addEventListener("click", closeVehicleDialog);
}

for (const button of document.querySelectorAll("[data-close-status-dialog]")) {
    button.addEventListener("click", closeStatusDialog);
}

initialize();
