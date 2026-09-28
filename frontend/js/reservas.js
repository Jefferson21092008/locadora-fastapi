import {
    ApiError,
    Permissions,
    applyNavigationPermissions,
    cancelReservation,
    clearToken,
    createReservation,
    getCurrentUser,
    getVehicles,
    hasPermission,
    logout,
    queryReservations,
    restoreSession,
} from "/app/js/api.js";

const roleBadge = document.querySelector("#current-role");
const logoutButton = document.querySelector("#logout-button");
const newReservationButton = document.querySelector("#new-reservation-button");
const refreshButton = document.querySelector("#refresh-reservations-button");
const searchInput = document.querySelector("#reservation-search");
const statusFilter = document.querySelector("#reservation-status-filter");
const orderSelect = document.querySelector("#reservation-order");
const pageSizeSelect = document.querySelector("#reservation-page-size");
const previousPageButton = document.querySelector("#reservations-page-previous");
const nextPageButton = document.querySelector("#reservations-page-next");
const pageLabel = document.querySelector("#reservations-page-label");
const resultsCount = document.querySelector("#reservations-results-count");
const clearFiltersButton = document.querySelector("#clear-reservation-filters");
const pageMessage = document.querySelector("#reservations-message");
const loadingState = document.querySelector("#reservations-loading");
const emptyState = document.querySelector("#reservations-empty");
const emptyText = document.querySelector("#reservations-empty-text");
const reservationsList = document.querySelector("#reservations-list");
const description = document.querySelector("#reservations-description");

const reservationDialog = document.querySelector("#reservation-dialog");
const reservationForm = document.querySelector("#reservation-form");
const reservationVehicleInput = document.querySelector("#reservation-vehicle");
const reservationStartInput = document.querySelector("#reservation-start");
const reservationEndInput = document.querySelector("#reservation-end");
const reservationFormMessage = document.querySelector("#reservation-form-message");
const saveReservationButton = document.querySelector("#save-reservation-button");

const summaryElements = {
    total: document.querySelector("#reservations-summary-total"),
    active: document.querySelector("#reservations-summary-active"),
    expired: document.querySelector("#reservations-summary-expired"),
    cancelled: document.querySelector("#reservations-summary-cancelled"),
    converted: document.querySelector("#reservations-summary-converted"),
};

let currentUser = null;
let reservations = [];
let vehicles = [];
let searchTimer = null;
let savingReservation = false;
let pagination = {
    pagina: 1,
    total: 0,
    total_paginas: 0,
};

function goToLogin() {
    window.location.replace("/app/");
}

function goToDashboard() {
    window.location.replace("/app/dashboard.html");
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

function formatDate(value) {
    if (!value) {
        return "—";
    }

    const parsedDate = new Date(`${value}T00:00:00`);
    return Number.isNaN(parsedDate.getTime())
        ? value
        : parsedDate.toLocaleDateString("pt-BR");
}

function tomorrowIsoDate() {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);

    const year = tomorrow.getFullYear();
    const month = String(tomorrow.getMonth() + 1).padStart(2, "0");
    const day = String(tomorrow.getDate()).padStart(2, "0");

    return `${year}-${month}-${day}`;
}

function showMessage(element, text, type = "error") {
    element.textContent = text;
    element.classList.add(
        "form-message--visible",
        `form-message--${type}`,
    );
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
    return hasPermission(
        currentUser,
        permission,
    );
}

function canReadAllReservations() {
    return can(
        Permissions.RESERVAS_LER
    );
}

function configureCurrentUser(user) {
    currentUser = user;
    roleBadge.textContent = (
        user.role === "admin"
            ? "Administrador"
            : "Cliente"
    );
    applyNavigationPermissions(user);

    newReservationButton.hidden = !can(
        Permissions.RESERVAS_CRIAR
    );

    if (canReadAllReservations()) {
        description.textContent = (
            "Acompanhe reservas de todos os clientes e os períodos comprometidos da frota."
        );
    }

    if (
        !canReadAllReservations()
        && !can(
            Permissions.RESERVAS_PROPRIAS_LER
        )
    ) {
        goToDashboard();
    }
}

function updateSummary(summary) {
    const values = {
        total: summary.total,
        active: summary.ativas,
        expired: summary.expiradas,
        cancelled: summary.canceladas,
        converted: summary.convertidas,
    };

    for (const [name, element] of Object.entries(summaryElements)) {
        element.textContent = Number(
            values[name] ?? 0
        ).toLocaleString("pt-BR");
    }
}

function updatePagination() {
    const current = (
        pagination.total_paginas === 0
            ? 0
            : pagination.pagina
    );

    pageLabel.textContent = (
        `Página ${current} de ${pagination.total_paginas}`
    );
    previousPageButton.disabled = (
        pagination.pagina <= 1
    );
    nextPageButton.disabled = (
        pagination.pagina
        >= pagination.total_paginas
    );
}

function statusLabel(status) {
    const labels = {
        ativa: "Ativa",
        expirada: "Expirada",
        cancelada: "Cancelada",
        convertida: "Convertida em aluguel",
    };

    return labels[status] ?? status;
}

function cancelAction(reservation) {
    if (
        !can(Permissions.RESERVAS_CANCELAR)
        || reservation.status !== "ativa"
    ) {
        return "";
    }

    return `
        <button
            class="card-button card-button--danger"
            type="button"
            data-action="cancel"
            data-id="${reservation.id}"
        >
            Cancelar reserva
        </button>
    `;
}

function renderReservations() {
    const hasActiveFilters = (
        searchInput.value.trim() !== ""
        || statusFilter.value !== "todos"
    );

    resultsCount.textContent = (
        `${reservations.length.toLocaleString("pt-BR")} nesta página · `
        + `${pagination.total.toLocaleString("pt-BR")} resultados`
    );
    clearFiltersButton.hidden = !hasActiveFilters;
    emptyState.hidden = reservations.length > 0;

    if (reservations.length === 0) {
        emptyText.textContent = (
            !hasActiveFilters
            && pagination.total === 0
                ? "Ainda não há reservas registradas."
                : "Altere a busca ou o filtro para visualizar outros resultados."
        );
    }

    reservationsList.innerHTML = reservations.map((reservation) => {
        const action = cancelAction(
            reservation
        );

        return `
            <article class="reservation-card">
                <div class="reservation-card__header">
                    <div>
                        <span class="reservation-card__id">Reserva #${reservation.id}</span>
                        <h3>${escapeHtml(reservation.veiculo_modelo)}</h3>
                        <p>${escapeHtml(reservation.veiculo_tipo)} · veículo #${reservation.veiculo_id}</p>
                    </div>
                    <span class="reservation-status reservation-status--${escapeHtml(reservation.status)}">
                        ${escapeHtml(statusLabel(reservation.status))}
                    </span>
                </div>

                <dl class="reservation-card__details">
                    <div>
                        <dt>Retirada</dt>
                        <dd>${formatDate(reservation.data_inicio)}</dd>
                    </div>
                    <div>
                        <dt>Devolução prevista</dt>
                        <dd>${formatDate(reservation.data_fim)}</dd>
                    </div>
                    ${canReadAllReservations() ? `
                        <div>
                            <dt>Cliente</dt>
                            <dd>${escapeHtml(reservation.cliente_nome)}</dd>
                        </div>
                        <div>
                            <dt>Usuário</dt>
                            <dd>@${escapeHtml(reservation.cliente_usuario)}</dd>
                        </div>
                    ` : ""}
                </dl>

                ${action ? `<div class="reservation-card__actions">${action}</div>` : ""}
            </article>
        `;
    }).join("");

    for (const button of reservationsList.querySelectorAll('[data-action="cancel"]')) {
        button.addEventListener(
            "click",
            handleCancelAction,
        );
    }
}

function populateVehicleOptions() {
    const reservable = vehicles
        .filter(
            (vehicle) => (
                vehicle.status !== "desativado"
            ),
        )
        .sort(
            (first, second) => (
                first.modelo.localeCompare(
                    second.modelo,
                    "pt-BR",
                )
            ),
        );

    reservationVehicleInput.innerHTML = `
        <option value="">Selecione um veículo</option>
        ${reservable.map((vehicle) => `
            <option value="${vehicle.id}">
                ${escapeHtml(vehicle.modelo)} · ${escapeHtml(vehicle.tipo)}
            </option>
        `).join("")}
    `;
}

function queryParams() {
    const [ordenar, direcao] = orderSelect.value.split(":");

    return {
        pagina: pagination.pagina,
        por_pagina: Number(
            pageSizeSelect.value
        ),
        busca: searchInput.value.trim(),
        status: statusFilter.value,
        ordenar,
        direcao,
    };
}

async function loadReservations() {
    loadingState.hidden = false;
    emptyState.hidden = true;
    clearMessage(pageMessage);

    try {
        const response = await queryReservations(
            queryParams(),
            !canReadAllReservations(),
        );

        reservations = response.items;
        pagination = {
            pagina: response.pagina,
            total: response.total,
            total_paginas: response.total_paginas,
        };

        updateSummary(
            response.resumo
        );
        updatePagination();
        renderReservations();
    } catch (error) {
        if (
            error instanceof ApiError
            && error.status === 401
        ) {
            clearToken();
            goToLogin();
            return;
        }

        showMessage(
            pageMessage,
            error.message
            ?? "Não foi possível carregar as reservas.",
        );
    } finally {
        loadingState.hidden = true;
    }
}

function openReservationDialog() {
    reservationForm.reset();
    clearMessage(
        reservationFormMessage
    );

    const minimum = tomorrowIsoDate();
    reservationStartInput.min = minimum;
    reservationEndInput.min = minimum;
    reservationStartInput.value = minimum;

    const defaultEnd = new Date(
        `${minimum}T00:00:00`,
    );
    defaultEnd.setDate(
        defaultEnd.getDate() + 1
    );
    reservationEndInput.value = (
        defaultEnd
        .toISOString()
        .slice(0, 10)
    );

    reservationDialog.showModal();
}

function closeReservationDialog() {
    reservationDialog.close();
}

async function handleReservationSubmit(event) {
    event.preventDefault();

    if (savingReservation) {
        return;
    }

    clearMessage(
        reservationFormMessage
    );

    if (
        reservationEndInput.value
        <= reservationStartInput.value
    ) {
        showMessage(
            reservationFormMessage,
            "A devolução precisa ser posterior à retirada.",
        );
        return;
    }

    savingReservation = true;
    saveReservationButton.disabled = true;

    try {
        await createReservation(
            {
                id_veiculo: Number(
                    reservationVehicleInput.value
                ),
                data_inicio: (
                    reservationStartInput.value
                ),
                data_fim: (
                    reservationEndInput.value
                ),
            },
        );

        closeReservationDialog();
        pagination.pagina = 1;
        await loadReservations();

        showMessage(
            pageMessage,
            "Reserva criada com sucesso.",
            "success",
        );
    } catch (error) {
        showMessage(
            reservationFormMessage,
            error.message
            ?? "Não foi possível criar a reserva.",
        );
    } finally {
        savingReservation = false;
        saveReservationButton.disabled = false;
    }
}

async function handleCancelAction(event) {
    const id = Number(
        event.currentTarget.dataset.id
    );

    if (
        !window.confirm(
            "Deseja cancelar esta reserva?",
        )
    ) {
        return;
    }

    try {
        await cancelReservation(
            id,
            !canReadAllReservations(),
        );
        await loadReservations();
        showMessage(
            pageMessage,
            "Reserva cancelada com sucesso.",
            "success",
        );
    } catch (error) {
        showMessage(
            pageMessage,
            error.message
            ?? "Não foi possível cancelar a reserva.",
        );
    }
}

function resetFilters() {
    searchInput.value = "";
    statusFilter.value = "todos";
    orderSelect.value = "data_inicio:asc";
    pagination.pagina = 1;
    loadReservations();
}

async function initialize() {
    const restored = await restoreSession();

    if (!restored) {
        goToLogin();
        return;
    }

    try {
        const [user, vehicleList] = await Promise.all(
            [
                getCurrentUser(),
                getVehicles(),
            ],
        );

        configureCurrentUser(
            user
        );
        vehicles = vehicleList;
        populateVehicleOptions();
        await loadReservations();
    } catch (error) {
        if (
            error instanceof ApiError
            && error.status === 401
        ) {
            goToLogin();
            return;
        }

        showMessage(
            pageMessage,
            error.message
            ?? "Não foi possível preparar a página.",
        );
    }
}

newReservationButton.addEventListener(
    "click",
    openReservationDialog,
);

for (const button of document.querySelectorAll("[data-close-reservation-dialog]")) {
    button.addEventListener(
        "click",
        closeReservationDialog,
    );
}

reservationStartInput.addEventListener(
    "change",
    () => {
        reservationEndInput.min = (
            reservationStartInput.value
            || tomorrowIsoDate()
        );

        if (
            reservationEndInput.value
            <= reservationStartInput.value
        ) {
            reservationEndInput.value = "";
        }
    },
);

reservationForm.addEventListener(
    "submit",
    handleReservationSubmit,
);

refreshButton.addEventListener(
    "click",
    loadReservations,
);

clearFiltersButton.addEventListener(
    "click",
    resetFilters,
);

statusFilter.addEventListener(
    "change",
    () => {
        pagination.pagina = 1;
        loadReservations();
    },
);

orderSelect.addEventListener(
    "change",
    () => {
        pagination.pagina = 1;
        loadReservations();
    },
);

pageSizeSelect.addEventListener(
    "change",
    () => {
        pagination.pagina = 1;
        loadReservations();
    },
);

searchInput.addEventListener(
    "input",
    () => {
        window.clearTimeout(
            searchTimer
        );
        searchTimer = window.setTimeout(
            () => {
                pagination.pagina = 1;
                loadReservations();
            },
            300,
        );
    },
);

previousPageButton.addEventListener(
    "click",
    () => {
        if (pagination.pagina <= 1) {
            return;
        }

        pagination.pagina -= 1;
        loadReservations();
    },
);

nextPageButton.addEventListener(
    "click",
    () => {
        if (
            pagination.pagina
            >= pagination.total_paginas
        ) {
            return;
        }

        pagination.pagina += 1;
        loadReservations();
    },
);

logoutButton.addEventListener(
    "click",
    async () => {
        try {
            await logout();
        } finally {
            goToLogin();
        }
    },
);

initialize();
