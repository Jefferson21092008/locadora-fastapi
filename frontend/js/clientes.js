import {
    ApiError,
    clearToken,
    deactivateClient,
    getClients,
    getCurrentUser,
    getToken,
    reactivateClient,
} from "/app/js/api.js";

const roleBadge = document.querySelector("#current-role");
const logoutButton = document.querySelector("#logout-button");
const refreshButton = document.querySelector("#refresh-clients-button");
const searchInput = document.querySelector("#client-search");
const statusFilter = document.querySelector("#client-status-filter");
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

let clients = [];
let pendingClient = null;

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

function updateSummary() {
    const activeClients = clients.filter((client) => client.ativo).length;
    const counts = {
        total: clients.length,
        active: activeClients,
        inactive: clients.length - activeClients,
    };

    for (const [name, element] of Object.entries(summaryElements)) {
        element.textContent = counts[name].toLocaleString("pt-BR");
    }
}

function filteredClients() {
    const query = normalizeText(searchInput.value);
    const selectedStatus = statusFilter.value;

    return clients.filter((client) => {
        const clientStatus = client.ativo ? "ativo" : "desativado";
        const matchesStatus = selectedStatus === "todos" || selectedStatus === clientStatus;
        const searchableText = normalizeText(
            `${client.id} ${client.nome} ${client.usuario} ${client.email}`,
        );

        return matchesStatus && searchableText.includes(query);
    });
}

function renderClients() {
    const results = filteredClients();
    emptyState.hidden = results.length > 0;

    if (results.length === 0) {
        emptyText.textContent = clients.length === 0
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
        clients = await getClients();
        updateSummary();
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
    if (!getToken()) {
        goToLogin();
        return;
    }

    try {
        const currentUser = await getCurrentUser();
        if (currentUser.role !== "admin") {
            goToDashboard();
            return;
        }

        roleBadge.textContent = "Administrador";
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

logoutButton.addEventListener("click", () => {
    clearToken();
    goToLogin();
});

refreshButton.addEventListener("click", () => loadClients());
searchInput.addEventListener("input", renderClients);
statusFilter.addEventListener("change", renderClients);
confirmStatusButton.addEventListener("click", confirmStatusChange);

for (const button of document.querySelectorAll("[data-close-client-status]")) {
    button.addEventListener("click", closeStatusDialog);
}

initialize();
