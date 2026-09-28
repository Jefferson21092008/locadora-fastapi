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
    updateMaintenance,
} from "/app/js/api.js";

const roleBadge = document.querySelector("#current-role");
const logoutButton = document.querySelector("#logout-button");
const newMaintenanceButton = document.querySelector("#new-maintenance-button");
const refreshButton = document.querySelector("#refresh-maintenances-button");
const searchInput = document.querySelector("#maintenance-search");
const statusFilter = document.querySelector("#maintenance-status-filter");
const typeFilter = document.querySelector("#maintenance-type-filter");
const priorityFilter = document.querySelector("#maintenance-priority-filter");
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
const maintenanceDialogTitle = document.querySelector("#maintenance-dialog-title");
const maintenanceDialogEyebrow = document.querySelector("#maintenance-dialog-eyebrow");
const maintenanceVehicleInput = document.querySelector("#maintenance-vehicle");
const maintenanceTypeInput = document.querySelector("#maintenance-type");
const maintenancePriorityInput = document.querySelector("#maintenance-priority");
const maintenanceReasonInput = document.querySelector("#maintenance-reason");
const maintenanceProviderInput = document.querySelector("#maintenance-provider");
const maintenanceEstimatedCostInput = document.querySelector("#maintenance-estimated-cost");
const maintenanceExpectedDateInput = document.querySelector("#maintenance-expected-date");
const maintenanceNotesInput = document.querySelector("#maintenance-notes");
const maintenanceFormMessage = document.querySelector("#maintenance-form-message");
const saveMaintenanceButton = document.querySelector("#save-maintenance-button");
const saveMaintenanceLabel = document.querySelector("#save-maintenance-label");

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
    overdue: document.querySelector("#maintenances-summary-overdue"),
    estimated: document.querySelector("#maintenances-summary-estimated"),
    finished: document.querySelector("#maintenances-summary-finished"),
    cost: document.querySelector("#maintenances-summary-cost"),
};

let currentUser = null;
let maintenances = [];
let vehicles = [];
let pendingMaintenance = null;
let editingMaintenance = null;
let savingMaintenance = false;
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

    return String(value ?? "").replace(
        /[&<>"']/g,
        (character) => characters[character],
    );
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

function formatDate(value, fallback = "Em andamento") {
    if (!value) {
        return fallback;
    }

    const parsedDate = new Date(`${value}T00:00:00`);
    return Number.isNaN(parsedDate.getTime())
        ? value
        : parsedDate.toLocaleDateString("pt-BR");
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

function typeLabel(type) {
    return type === "preventiva" ? "Preventiva" : "Corretiva";
}

function priorityLabel(priority) {
    const labels = {
        baixa: "Baixa",
        media: "Média",
        alta: "Alta",
    };
    return labels[priority] ?? priority;
}

function updateSummary(resumo) {
    const counts = {
        total: Number(resumo.total ?? 0).toLocaleString("pt-BR"),
        active: Number(resumo.ativas ?? 0).toLocaleString("pt-BR"),
        overdue: Number(resumo.atrasadas ?? 0).toLocaleString("pt-BR"),
        estimated: formatCurrency(resumo.custo_estimado_ativo),
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

function renderMaintenances() {
    const hasActiveFilters = Boolean(normalizeText(searchInput.value))
        || statusFilter.value !== "todos"
        || typeFilter.value !== "todos"
        || priorityFilter.value !== "todos";

    resultsCount.textContent = `${maintenances.length.toLocaleString("pt-BR")} nesta página · ${pagination.total.toLocaleString("pt-BR")} resultados`;
    clearFiltersButton.hidden = !hasActiveFilters;
    emptyState.hidden = maintenances.length > 0;

    if (maintenances.length === 0) {
        emptyText.textContent = !hasActiveFilters && pagination.total === 0
            ? "Ainda não há manutenções registradas na locadora."
            : "Altere a busca ou os filtros para visualizar outros resultados.";
    }

    maintenancesList.innerHTML = maintenances.map((maintenance) => {
        const vehicle = findVehicle(maintenance.veiculo_id);
        const active = maintenance.status === "ativa";
        const statusLabel = active ? "Em andamento" : "Finalizada";
        const vehicleType = vehicle?.tipo ?? "veículo";
        const vehicleDetails = vehicle
            ? `ID ${vehicle.id} · ${vehicle.ano}`
            : `ID ${maintenance.veiculo_id}`;
        const overdue = Boolean(maintenance.atrasada);
        const canEdit = active
            && hasPermission(currentUser, Permissions.MANUTENCOES_EDITAR);
        const canFinish = active
            && hasPermission(currentUser, Permissions.MANUTENCOES_FINALIZAR);

        return `
            <article class="maintenance-card maintenance-card--${escapeHtml(maintenance.status)}${overdue ? " maintenance-card--overdue" : ""}">
                <div class="maintenance-card__main">
                    <div class="maintenance-card__header">
                        <span class="maintenance-card__id">Manutenção #${maintenance.id}</span>
                        <div class="maintenance-card__badges">
                            <span class="maintenance-badge maintenance-badge--type">
                                ${escapeHtml(typeLabel(maintenance.tipo))}
                            </span>
                            <span class="maintenance-badge maintenance-badge--priority-${escapeHtml(maintenance.prioridade)}">
                                ${escapeHtml(priorityLabel(maintenance.prioridade))}
                            </span>
                            ${overdue ? '<span class="maintenance-badge maintenance-badge--overdue">Atrasada</span>' : ""}
                            <span class="maintenance-status maintenance-status--${escapeHtml(maintenance.status)}">
                                ${statusLabel}
                            </span>
                        </div>
                    </div>

                    <div class="maintenance-card__vehicle">
                        <span>${escapeHtml(vehicleType)}</span>
                        <h3>${escapeHtml(vehicleLabel(maintenance.veiculo_id))}</h3>
                        <small>${escapeHtml(vehicleDetails)}</small>
                    </div>

                    <p class="maintenance-card__reason">${escapeHtml(maintenance.motivo)}</p>
                    ${maintenance.observacoes ? `
                        <p class="maintenance-card__notes">
                            ${escapeHtml(maintenance.observacoes)}
                        </p>
                    ` : ""}
                </div>

                <dl class="maintenance-card__details">
                    <div>
                        <dt>Entrada</dt>
                        <dd>${escapeHtml(formatDate(maintenance.data_inicio))}</dd>
                    </div>
                    <div>
                        <dt>Previsão</dt>
                        <dd>${escapeHtml(formatDate(maintenance.data_prevista, "Sem previsão"))}</dd>
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
                        <dt>Fornecedor</dt>
                        <dd>${escapeHtml(maintenance.fornecedor || "Não informado")}</dd>
                    </div>
                    <div>
                        <dt>Estimativa</dt>
                        <dd>${escapeHtml(formatCurrency(maintenance.custo_estimado))}</dd>
                    </div>
                    <div>
                        <dt>Custo real</dt>
                        <dd>${active ? "Pendente" : escapeHtml(formatCurrency(maintenance.custo))}</dd>
                    </div>
                </dl>

                <div class="maintenance-card__actions">
                    ${canEdit ? `
                        <button class="card-button" type="button" data-edit-maintenance="${maintenance.id}">
                            Editar
                        </button>
                    ` : ""}
                    ${canFinish ? `
                        <button class="card-button card-button--success" type="button" data-finish-maintenance="${maintenance.id}">
                            Finalizar serviço
                        </button>
                    ` : (!active ? '<span class="maintenance-card__finished-note">Serviço concluído</span>' : "")}
                </div>
            </article>
        `;
    }).join("");

    for (const button of maintenancesList.querySelectorAll("[data-edit-maintenance]")) {
        button.addEventListener("click", openEditDialog);
    }

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

function resetMaintenanceDialog() {
    editingMaintenance = null;
    maintenanceForm.reset();
    maintenanceTypeInput.value = "corretiva";
    maintenancePriorityInput.value = "media";
    maintenanceEstimatedCostInput.value = "0";
    maintenanceExpectedDateInput.min = new Date().toISOString().slice(0, 10);
    maintenanceDialogEyebrow.textContent = "Entrada na oficina";
    maintenanceDialogTitle.textContent = "Abrir manutenção";
    saveMaintenanceLabel.textContent = "Abrir manutenção";
    populateAvailableVehicles();
}

function openMaintenanceDialog() {
    const hasAvailableVehicle = vehicles.some(
        (vehicle) => vehicle.status === "disponivel",
    );

    if (!hasAvailableVehicle) {
        showMessage(
            pageMessage,
            "Não há veículos disponíveis para iniciar uma manutenção.",
        );
        return;
    }

    resetMaintenanceDialog();
    clearMessage(maintenanceFormMessage);
    maintenanceDialog.showModal();
    maintenanceVehicleInput.focus();
}

function openEditDialog(event) {
    const maintenanceId = Number(event.currentTarget.dataset.editMaintenance);
    editingMaintenance = maintenances.find(
        (maintenance) => maintenance.id === maintenanceId,
    );

    if (!editingMaintenance) {
        return;
    }

    const vehicle = findVehicle(editingMaintenance.veiculo_id);
    maintenanceForm.reset();
    clearMessage(maintenanceFormMessage);

    maintenanceVehicleInput.innerHTML = `
        <option value="${editingMaintenance.veiculo_id}">
            ${escapeHtml(vehicleLabel(editingMaintenance.veiculo_id))}
        </option>
    `;
    maintenanceVehicleInput.value = String(editingMaintenance.veiculo_id);
    maintenanceVehicleInput.disabled = true;

    maintenanceTypeInput.value = editingMaintenance.tipo;
    maintenancePriorityInput.value = editingMaintenance.prioridade;
    maintenanceReasonInput.value = editingMaintenance.motivo;
    maintenanceProviderInput.value = editingMaintenance.fornecedor ?? "";
    maintenanceEstimatedCostInput.value = String(
        Number(editingMaintenance.custo_estimado ?? 0),
    );
    maintenanceExpectedDateInput.value = editingMaintenance.data_prevista ?? "";
    maintenanceExpectedDateInput.min = editingMaintenance.data_inicio;
    maintenanceNotesInput.value = editingMaintenance.observacoes ?? "";

    maintenanceDialogEyebrow.textContent = "Acompanhamento da oficina";
    maintenanceDialogTitle.textContent = `Editar manutenção #${editingMaintenance.id}`;
    saveMaintenanceLabel.textContent = "Salvar alterações";
    saveMaintenanceButton.disabled = false;

    if (vehicle) {
        maintenanceVehicleInput.options[0].textContent = `${vehicle.modelo} · ${vehicle.tipo} · ${vehicle.ano}`;
    }

    maintenanceDialog.showModal();
    maintenanceReasonInput.focus();
}

function closeMaintenanceDialog() {
    if (savingMaintenance) {
        return;
    }

    maintenanceDialog.close();
    resetMaintenanceDialog();
}

function maintenanceDetailsPayload() {
    return {
        motivo: maintenanceReasonInput.value.trim(),
        tipo: maintenanceTypeInput.value,
        prioridade: maintenancePriorityInput.value,
        fornecedor: maintenanceProviderInput.value.trim() || null,
        custo_estimado: Number(maintenanceEstimatedCostInput.value || 0),
        data_prevista: maintenanceExpectedDateInput.value || null,
        observacoes: maintenanceNotesInput.value.trim() || null,
    };
}

async function submitMaintenance(event) {
    event.preventDefault();
    clearMessage(maintenanceFormMessage);
    savingMaintenance = true;
    saveMaintenanceButton.disabled = true;

    try {
        const details = maintenanceDetailsPayload();

        if (editingMaintenance) {
            await updateMaintenance(
                editingMaintenance.id,
                details,
            );
            showMessage(
                pageMessage,
                "Manutenção atualizada com sucesso.",
                "success",
            );
        } else {
            await createMaintenance({
                id_veiculo: Number(maintenanceVehicleInput.value),
                ...details,
            });
            showMessage(
                pageMessage,
                "Manutenção aberta com sucesso.",
                "success",
            );
        }

        maintenanceDialog.close();
        editingMaintenance = null;
        await loadData({ preserveMessage: true });
    } catch (error) {
        if (error instanceof ApiError && error.status === 401) {
            clearToken();
            goToLogin();
            return;
        }

        showMessage(maintenanceFormMessage, error.message);
    } finally {
        savingMaintenance = false;
        saveMaintenanceButton.disabled = false;
    }
}

function openFinishDialog(event) {
    const maintenanceId = Number(event.currentTarget.dataset.finishMaintenance);
    pendingMaintenance = maintenances.find(
        (maintenance) => maintenance.id === maintenanceId,
    );
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
        showMessage(
            pageMessage,
            "Manutenção finalizada e veículo liberado com sucesso.",
            "success",
        );
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
                tipo: typeFilter.value,
                prioridade: priorityFilter.value,
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

function resetFilters() {
    searchInput.value = "";
    statusFilter.value = "todos";
    typeFilter.value = "todos";
    priorityFilter.value = "todos";
    pagination.pagina = 1;
    loadData();
    searchInput.focus();
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

for (const filter of [
    statusFilter,
    typeFilter,
    priorityFilter,
    orderSelect,
    pageSizeSelect,
]) {
    filter.addEventListener("change", () => {
        pagination.pagina = 1;
        loadData();
    });
}

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

clearFiltersButton.addEventListener("click", resetFilters);
maintenanceForm.addEventListener("submit", submitMaintenance);
finishForm.addEventListener("submit", submitFinishMaintenance);

for (const button of document.querySelectorAll("[data-close-maintenance-dialog]")) {
    button.addEventListener("click", closeMaintenanceDialog);
}

for (const button of document.querySelectorAll("[data-close-finish-maintenance]")) {
    button.addEventListener("click", closeFinishDialog);
}

initialize();
