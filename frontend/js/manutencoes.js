import {
    ApiError,
    Permissions,
    applyNavigationPermissions,
    clearToken,
    createMaintenance,
    finishMaintenance,
    getCurrentUser,
    queryMaintenances,
    restoreSession,
    hasPermission,
    logout,
    getVehicles,
} from "/app/js/api.js";

const roleBadge = document.querySelector("#current-role");
const logoutButton = document.querySelector("#logout-button");
const newMaintenanceButton = document.querySelector("#new-maintenance-button");
const refreshButton = document.querySelector("#refresh-maintenances-button");
const searchInput = document.querySelector("#maintenance-search");
const statusFilter = document.querySelector("#maintenance-status-filter");
const orderSelect = document.querySelector("#maintenance-order");
const pageSizeSelect = document.querySelector("#maintenance-page-size");
const previousPageButton = document.querySelector("#maintenances-page-previous");
const nextPageButton = document.querySelector("#maintenances-page-next");
const pageLabel = document.querySelector("#maintenances-page-label");
const resultsCount = document.querySelector("#maintenances-results-count");
const clearFiltersButton = document.querySelector("#clear-maintenance-filters");
const pageMessage = document.querySelector("#maintenances-message");
const loadingState = document.querySelector("#maintenances-loading");
const emptyState = document.querySelector("#maintenances-empty");
const emptyText = document.querySelector("#maintenances-empty-text");
const maintenancesList = document.querySelector("#maintenances-list");

const maintenanceDialog = document.querySelector("#maintenance-dialog");
const maintenanceForm = document.querySelector("#maintenance-form");
const maintenanceVehicleInput = document.querySelector("#maintenance-vehicle");
const maintenanceReasonInput = document.querySelector("#maintenance-reason");
const maintenanceFormMessage = document.querySelector("#maintenance-form-message");
const saveMaintenanceButton = document.querySelector("#save-maintenance-button");

const finishDialog = document.querySelector("#finish-maintenance-dialog");
const finishForm = document.querySelector("#finish-maintenance-form");
const finishTitle = document.querySelector("#finish-maintenance-title");
const finishDescription = document.querySelector("#finish-maintenance-description");
const maintenanceCostInput = document.querySelector("#maintenance-cost");
const finishMessage = document.querySelector("#finish-maintenance-message");
const confirmFinishButton = document.querySelector("#confirm-finish-maintenance");

const summaryElements = {
    total: document.querySelector("#maintenances-summary-total"),
    active: document.querySelector("#maintenances-summary-active"),
    finished: document.querySelector("#maintenances-summary-finished"),
    cost: document.querySelector("#maintenances-summary-cost"),
};

let currentUser = null;
let maintenances = [];
let vehicles = [];
let pendingMaintenance = null;
let searchTimer = null;
let pagination = { pagina: 1, total: 0, total_paginas: 0 };

function goToLogin() {
    window.location.replace("/app/");
}

function goToDashboard() {
    window.location.replace("/app/dashboard.html");
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

function formatDate(value) {
    if (!value) {
        return "Em andamento";
    }

    const date = new Date(`${value}T00:00:00`);
    return Number.isNaN(date.getTime())
        ? value
        : date.toLocaleDateString("pt-BR");
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

function findVehicle(vehicleId) {
    return vehicles.find((vehicle) => vehicle.id === Number(vehicleId));
}

function vehicleLabel(vehicleId) {
    const vehicle = findVehicle(vehicleId);
    return vehicle ? vehicle.modelo : `Veículo #${vehicleId}`;
}

function updateSummary(resumo) {
    const counts = {
        total: Number(resumo.total ?? 0).toLocaleString("pt-BR"),
        active: Number(resumo.ativas ?? 0).toLocaleString("pt-BR"),
        finished: Number(resumo.finalizadas ?? 0).toLocaleString("pt-BR"),
        cost: formatCurrency(resumo.custo_finalizado),
    };

    for (const [name, element] of Object.entries(summaryElements)) {
        element.textContent = counts[name];
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

function filteredMaintenances() {
    return maintenances;
}

function renderMaintenances() {
    const results = filteredMaintenances();
    const hasActiveFilters = Boolean(normalizeText(searchInput.value))
        || statusFilter.value !== "todos";

    resultsCount.textContent = `${results.length.toLocaleString("pt-BR")} nesta página · ${pagination.total.toLocaleString("pt-BR")} resultados`;
    clearFiltersButton.hidden = !hasActiveFilters;

    emptyState.hidden = results.length > 0;

    if (results.length === 0) {
        emptyText.textContent = !hasActiveFilters && pagination.total === 0
            ? "Ainda não há manutenções registradas na locadora."
            : "Altere a busca ou o filtro para visualizar outros resultados.";
    }

    maintenancesList.innerHTML = results.map((maintenance) => {
        const vehicle = findVehicle(maintenance.veiculo_id);
        const active = maintenance.status === "ativa";
        const statusLabel = active ? "Em andamento" : "Finalizada";
        const vehicleType = vehicle?.tipo ?? "veículo";
        const vehicleDetails = vehicle
            ? `ID ${vehicle.id} · ${vehicle.ano}`
            : `ID ${maintenance.veiculo_id}`;

        return `
            <article class="maintenance-card maintenance-card--${escapeHtml(maintenance.status)}">
                <div class="maintenance-card__main">
                    <div class="maintenance-card__header">
                        <span class="maintenance-card__id">Manutenção #${maintenance.id}</span>
                        <span class="maintenance-status maintenance-status--${escapeHtml(maintenance.status)}">
                            ${statusLabel}
                        </span>
                    </div>

                    <div class="maintenance-card__vehicle">
                        <span>${escapeHtml(vehicleType)}</span>
                        <h3>${escapeHtml(vehicleLabel(maintenance.veiculo_id))}</h3>
                        <small>${escapeHtml(vehicleDetails)}</small>
                    </div>

                    <p class="maintenance-card__reason">${escapeHtml(maintenance.motivo)}</p>
                </div>

                <dl class="maintenance-card__details">
                    <div>
                        <dt>Entrada</dt>
                        <dd>${escapeHtml(formatDate(maintenance.data_inicio))}</dd>
                    </div>
                    <div>
                        <dt>Saída</dt>
                        <dd>${escapeHtml(formatDate(maintenance.data_fim))}</dd>
                    </div>
                    <div>
                        <dt>Quilometragem</dt>
                        <dd>${escapeHtml(formatDistance(maintenance.quilometragem))}</dd>
                    </div>
                    <div>
                        <dt>Custo</dt>
                        <dd>${active ? "Pendente" : escapeHtml(formatCurrency(maintenance.custo))}</dd>
                    </div>
                </dl>

                <div class="maintenance-card__actions">
                    ${active && hasPermission(currentUser, Permissions.MANUTENCOES_FINALIZAR) ? `
                        <button class="card-button card-button--success" type="button" data-finish-maintenance="${maintenance.id}">
                            Finalizar serviço
                        </button>
                    ` : (!active ? '<span class="maintenance-card__finished-note">Serviço concluído</span>' : "")}
                </div>
            </article>
        `;
    }).join("");

    for (const button of maintenancesList.querySelectorAll("[data-finish-maintenance]")) {
        button.addEventListener("click", openFinishDialog);
    }
}

function populateAvailableVehicles() {
    const availableVehicles = vehicles
        .filter((vehicle) => vehicle.status === "disponivel")
        .sort((first, second) => first.modelo.localeCompare(second.modelo, "pt-BR"));

    maintenanceVehicleInput.innerHTML = [
        '<option value="">Selecione um veículo</option>',
        ...availableVehicles.map((vehicle) => `
            <option value="${vehicle.id}">
                ${escapeHtml(vehicle.modelo)} · ${escapeHtml(vehicle.tipo)} · ${vehicle.ano} · ${escapeHtml(formatDistance(vehicle.quilometragem))}
            </option>
        `),
    ].join("");

    maintenanceVehicleInput.disabled = availableVehicles.length === 0;
    saveMaintenanceButton.disabled = availableVehicles.length === 0;
}

function openMaintenanceDialog() {
    const hasAvailableVehicle = vehicles.some((vehicle) => vehicle.status === "disponivel");
    if (!hasAvailableVehicle) {
        showMessage(pageMessage, "Não há veículos disponíveis para iniciar uma manutenção.");
        return;
    }

    maintenanceForm.reset();
    clearMessage(maintenanceFormMessage);
    maintenanceDialog.showModal();
    maintenanceVehicleInput.focus();
}

function closeMaintenanceDialog() {
    if (!saveMaintenanceButton.disabled) {
        maintenanceDialog.close();
    }
}

async function submitMaintenance(event) {
    event.preventDefault();
    clearMessage(maintenanceFormMessage);
    saveMaintenanceButton.disabled = true;

    try {
        await createMaintenance({
            id_veiculo: Number(maintenanceVehicleInput.value),
            motivo: maintenanceReasonInput.value.trim(),
        });

        maintenanceDialog.close();
        showMessage(pageMessage, "Manutenção aberta com sucesso.", "success");
        await loadData({ preserveMessage: true });
    } catch (error) {
        if (error instanceof ApiError && error.status === 401) {
            clearToken();
            goToLogin();
            return;
        }

        showMessage(maintenanceFormMessage, error.message);
    } finally {
        saveMaintenanceButton.disabled = false;
    }
}

function openFinishDialog(event) {
    const maintenanceId = Number(event.currentTarget.dataset.finishMaintenance);
    pendingMaintenance = maintenances.find((maintenance) => maintenance.id === maintenanceId);
    if (!pendingMaintenance) {
        return;
    }

    finishForm.reset();
    clearMessage(finishMessage);
    finishTitle.textContent = `Finalizar ${vehicleLabel(pendingMaintenance.veiculo_id)}`;
    finishDescription.textContent = "Informe o custo total do serviço. Ao finalizar, o veículo voltará a ficar disponível.";
    finishDialog.showModal();
    maintenanceCostInput.focus();
}

function closeFinishDialog() {
    if (!confirmFinishButton.disabled) {
        pendingMaintenance = null;
        finishDialog.close();
    }
}

async function submitFinishMaintenance(event) {
    event.preventDefault();
    if (!pendingMaintenance) {
        return;
    }

    clearMessage(finishMessage);
    confirmFinishButton.disabled = true;

    try {
        await finishMaintenance(pendingMaintenance.veiculo_id, {
            custo: Number(maintenanceCostInput.value),
        });

        finishDialog.close();
        pendingMaintenance = null;
        showMessage(pageMessage, "Manutenção finalizada e veículo liberado com sucesso.", "success");
        await loadData({ preserveMessage: true });
    } catch (error) {
        if (error instanceof ApiError && error.status === 401) {
            clearToken();
            goToLogin();
            return;
        }

        showMessage(finishMessage, error.message);
    } finally {
        confirmFinishButton.disabled = false;
    }
}

async function loadData({ preserveMessage = false } = {}) {
    if (!preserveMessage) {
        clearMessage(pageMessage);
    }

    loadingState.hidden = false;
    emptyState.hidden = true;
    maintenancesList.setAttribute("aria-busy", "true");
    refreshButton.disabled = true;

    try {
        const [result, loadedVehicles] = await Promise.all([
            queryMaintenances({
                pagina: pagination.pagina,
                por_pagina: Number(pageSizeSelect.value),
                busca: searchInput.value.trim(),
                status: statusFilter.value,
                ...orderParams(),
            }),
            getVehicles(),
        ]);

        if (result.total_paginas > 0 && pagination.pagina > result.total_paginas) {
            pagination.pagina = result.total_paginas;
            return loadData({ preserveMessage: true });
        }

        maintenances = result.items;
        vehicles = loadedVehicles;
        pagination = {
            pagina: result.pagina,
            total: result.total,
            total_paginas: result.total_paginas,
        };
        updateSummary(result.resumo);
        updatePagination();
        populateAvailableVehicles();
        renderMaintenances();
    } catch (error) {
        if (error instanceof ApiError && error.status === 401) {
            clearToken();
            goToLogin();
            return;
        }

        if (error instanceof ApiError && error.status === 403) {
            goToDashboard();
            return;
        }

        showMessage(pageMessage, error.message);
    } finally {
        loadingState.hidden = true;
        maintenancesList.removeAttribute("aria-busy");
        refreshButton.disabled = false;
    }
}

async function initialize() {
    if (!(await restoreSession())) {
        goToLogin();
        return;
    }

    try {
        currentUser = await getCurrentUser();
        if (!hasPermission(currentUser, Permissions.MANUTENCOES_LER)) {
            goToDashboard();
            return;
        }

        roleBadge.textContent = currentUser.role === "admin"
            ? "Administrador"
            : "Cliente";
        newMaintenanceButton.hidden = !hasPermission(
            currentUser,
            Permissions.MANUTENCOES_CRIAR,
        );
        applyNavigationPermissions(currentUser);
        await loadData();
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

newMaintenanceButton.addEventListener("click", openMaintenanceDialog);
refreshButton.addEventListener("click", () => loadData());
searchInput.addEventListener("input", () => {
    window.clearTimeout(searchTimer);
    searchTimer = window.setTimeout(() => {
        pagination.pagina = 1;
        loadData();
    }, 300);
});
statusFilter.addEventListener("change", () => {
    pagination.pagina = 1;
    loadData();
});
orderSelect.addEventListener("change", () => {
    pagination.pagina = 1;
    loadData();
});
pageSizeSelect.addEventListener("change", () => {
    pagination.pagina = 1;
    loadData();
});
previousPageButton.addEventListener("click", () => {
    if (pagination.pagina > 1) {
        pagination.pagina -= 1;
        loadData();
    }
});
nextPageButton.addEventListener("click", () => {
    if (pagination.pagina < pagination.total_paginas) {
        pagination.pagina += 1;
        loadData();
    }
});
clearFiltersButton.addEventListener("click", () => {
    searchInput.value = "";
    statusFilter.value = "todos";
    pagination.pagina = 1;
    loadData();
    searchInput.focus();
});
maintenanceForm.addEventListener("submit", submitMaintenance);
finishForm.addEventListener("submit", submitFinishMaintenance);

for (const button of document.querySelectorAll("[data-close-maintenance-dialog]")) {
    button.addEventListener("click", closeMaintenanceDialog);
}

for (const button of document.querySelectorAll("[data-close-finish-maintenance]")) {
    button.addEventListener("click", closeFinishDialog);
}

initialize();
