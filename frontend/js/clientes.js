import {
    ApiError,
    Permissions,
    applyNavigationPermissions,
    clearToken,
    deactivateClient,
    queryClients,
    getCurrentUser,
    restoreSession,
    hasPermission,
    logout,
    reactivateClient,
} from "/app/js/api.js";

const roleBadge = document.querySelector("#current-role");
const logoutButton = document.querySelector("#logout-button");
const refreshButton = document.querySelector("#refresh-clients-button");
const searchInput = document.querySelector("#client-search");
const statusFilter = document.querySelector("#client-status-filter");
const orderSelect = document.querySelector("#client-order");
const pageSizeSelect = document.querySelector("#client-page-size");
const previousPageButton = document.querySelector("#clients-page-previous");
const nextPageButton = document.querySelector("#clients-page-next");
const pageLabel = document.querySelector("#clients-page-label");
const resultsCount = document.querySelector("#clients-results-count");
const clearFiltersButton = document.querySelector("#clear-client-filters");
const pageMessage = document.querySelector("#clients-message");
const loadingState = document.querySelector("#clients-loading");
const emptyState = document.querySelector("#clients-empty");
const emptyText = document.querySelector("#clients-empty-text");
const clientsGrid = document.querySelector("#clients-grid");

const statusDialog = document.querySelector("#client-status-dialog");
const statusTitle = document.querySelector("#client-status-title");
const statusDescription = document.querySelector("#client-status-description");
const statusMessage = document.querySelector("#client-status-message");
const confirmStatusButton = document.querySelector("#confirm-client-status");

const summaryElements = {
    total: document.querySelector("#clients-summary-total"),
    active: document.querySelector("#clients-summary-active"),
    inactive: document.querySelector("#clients-summary-inactive"),
};

let currentUser = null;
let clients = [];
let pendingClient = null;
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

function clientInitials(name) {
    const words = String(name ?? "")
        .trim()
        .split(/\s+/)
        .filter(Boolean);

    if (words.length === 0) {
        return "?";
    }

    return words
        .slice(0, 2)
        .map((word) => word[0])
        .join("")
        .toUpperCase();
}

function updateSummary(resumo) {
    const counts = {
        total: resumo.total,
        active: resumo.ativos,
        inactive: resumo.desativados,
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

function filteredClients() {
    return clients;
}

function renderClients() {
    const results = filteredClients();
    const hasActiveFilters = Boolean(normalizeText(searchInput.value))
        || statusFilter.value !== "todos";

    resultsCount.textContent = `${results.length.toLocaleString("pt-BR")} nesta página · ${pagination.total.toLocaleString("pt-BR")} resultados`;
    clearFiltersButton.hidden = !hasActiveFilters;

    emptyState.hidden = results.length > 0;

    if (results.length === 0) {
        emptyText.textContent = !hasActiveFilters && pagination.total === 0
            ? "Ainda não há clientes cadastrados na locadora."
            : "Altere a busca ou o filtro para visualizar outros resultados.";
    }

    clientsGrid.innerHTML = results.map((client) => {
        const action = client.ativo ? "deactivate" : "reactivate";
        const actionLabel = client.ativo ? "Desativar" : "Reativar";
        const statusLabel = client.ativo ? "Ativo" : "Desativado";

        return `
            <article class="client-card ${client.ativo ? "" : "client-card--inactive"}">
                <div class="client-card__header">
                    <span class="client-avatar" aria-hidden="true">${escapeHtml(clientInitials(client.nome))}</span>
                    <span class="client-status client-status--${client.ativo ? "active" : "inactive"}">
                        ${statusLabel}
                    </span>
                </div>

                <div class="client-card__identity">
                    <h3>${escapeHtml(client.nome)}</h3>
                    <p>@${escapeHtml(client.usuario)}</p>
                </div>

                <dl class="client-card__details">
                    <div>
                        <dt>ID</dt>
                        <dd>${client.id}</dd>
                    </div>
                    <div>
                        <dt>E-mail</dt>
                        <dd>${escapeHtml(client.email)}</dd>
                    </div>
                </dl>

                ${hasPermission(currentUser, Permissions.CLIENTES_GERENCIAR_STATUS) ? `
                    <div class="client-card__actions">
                        <button
                            class="card-button ${client.ativo ? "card-button--danger" : "card-button--success"}"
                            type="button"
                            data-action="${action}"
                            data-id="${client.id}"
                        >
                            ${actionLabel}
                        </button>
                    </div>
                ` : ""}
            </article>
        `;
    }).join("");

    for (const button of clientsGrid.querySelectorAll("[data-action]")) {
        button.addEventListener("click", openStatusDialog);
    }
}

function findClient(clientId) {
    return clients.find((client) => client.id === Number(clientId));
}

function openStatusDialog(event) {
    const client = findClient(event.currentTarget.dataset.id);
    if (!client) {
        return;
    }

    pendingClient = client;
    clearMessage(statusMessage);

    if (client.ativo) {
        statusTitle.textContent = "Desativar cliente";
        statusDescription.textContent = `A conta de ${client.nome} perderá o acesso ao sistema. Clientes com aluguel ativo não podem ser desativados.`;
        confirmStatusButton.querySelector("span:first-child").textContent = "Desativar";
    } else {
        statusTitle.textContent = "Reativar cliente";
        statusDescription.textContent = `A conta de ${client.nome} voltará a ter acesso ao sistema.`;
        confirmStatusButton.querySelector("span:first-child").textContent = "Reativar";
    }

    statusDialog.showModal();
    confirmStatusButton.focus();
}

function closeStatusDialog() {
    if (!confirmStatusButton.disabled) {
        pendingClient = null;
        statusDialog.close();
    }
}

async function confirmStatusChange() {
    if (!pendingClient) {
        return;
    }

    clearMessage(statusMessage);
    confirmStatusButton.disabled = true;
    const deactivating = pendingClient.ativo;

    try {
        if (deactivating) {
            await deactivateClient(pendingClient.id);
        } else {
            await reactivateClient(pendingClient.id);
        }

        statusDialog.close();
        pendingClient = null;
        showMessage(
            pageMessage,
            deactivating ? "Cliente desativado com sucesso." : "Cliente reativado com sucesso.",
            "success",
        );
        await loadClients({ preserveMessage: true });
    } catch (error) {
        if (error instanceof ApiError && error.status === 401) {
            clearToken();
            goToLogin();
            return;
        }

        showMessage(statusMessage, error.message);
    } finally {
        confirmStatusButton.disabled = false;
    }
}

async function loadClients({ preserveMessage = false } = {}) {
    if (!preserveMessage) {
        clearMessage(pageMessage);
    }

    loadingState.hidden = false;
    emptyState.hidden = true;
    clientsGrid.setAttribute("aria-busy", "true");
    refreshButton.disabled = true;

    try {
        const result = await queryClients({
            pagina: pagination.pagina,
            por_pagina: Number(pageSizeSelect.value),
            busca: searchInput.value.trim(),
            status: statusFilter.value,
            ...orderParams(),
        });
        if (result.total_paginas > 0 && pagination.pagina > result.total_paginas) {
            pagination.pagina = result.total_paginas;
            return loadClients({ preserveMessage: true });
        }

        clients = result.items;
        pagination = {
            pagina: result.pagina,
            total: result.total,
            total_paginas: result.total_paginas,
        };
        updateSummary(result.resumo);
        updatePagination();
        renderClients();
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
        clientsGrid.removeAttribute("aria-busy");
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
        if (!hasPermission(currentUser, Permissions.CLIENTES_LER)) {
            goToDashboard();
            return;
        }

        roleBadge.textContent = currentUser.role === "admin"
            ? "Administrador"
            : "Cliente";
        applyNavigationPermissions(currentUser);
        await loadClients();
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

refreshButton.addEventListener("click", () => loadClients());
searchInput.addEventListener("input", () => {
    window.clearTimeout(searchTimer);
    searchTimer = window.setTimeout(() => {
        pagination.pagina = 1;
        loadClients();
    }, 300);
});
statusFilter.addEventListener("change", () => {
    pagination.pagina = 1;
    loadClients();
});
orderSelect.addEventListener("change", () => {
    pagination.pagina = 1;
    loadClients();
});
pageSizeSelect.addEventListener("change", () => {
    pagination.pagina = 1;
    loadClients();
});
previousPageButton.addEventListener("click", () => {
    if (pagination.pagina > 1) {
        pagination.pagina -= 1;
        loadClients();
    }
});
nextPageButton.addEventListener("click", () => {
    if (pagination.pagina < pagination.total_paginas) {
        pagination.pagina += 1;
        loadClients();
    }
});
clearFiltersButton.addEventListener("click", () => {
    searchInput.value = "";
    statusFilter.value = "todos";
    pagination.pagina = 1;
    loadClients();
    searchInput.focus();
});
confirmStatusButton.addEventListener("click", confirmStatusChange);

for (const button of document.querySelectorAll("[data-close-client-status]")) {
    button.addEventListener("click", closeStatusDialog);
}

initialize();
