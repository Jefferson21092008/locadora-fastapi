import {
    ApiError,
    Permissions,
    applyNavigationPermissions,
    clearToken,
    getAuditLogs,
    getCurrentUser,
    hasPermission,
    logout,
    restoreSession,
} from "/app/js/api.js";

const roleBadge = document.querySelector("#current-role");
const logoutButton = document.querySelector("#logout-button");
const refreshButton = document.querySelector("#refresh-audit-button");
const searchInput = document.querySelector("#audit-search");
const resourceFilter = document.querySelector("#audit-resource-filter");
const actionFilter = document.querySelector("#audit-action-filter");
const clearFiltersButton = document.querySelector("#clear-audit-filters");
const pageMessage = document.querySelector("#audit-message");
const loadingState = document.querySelector("#audit-loading");
const emptyState = document.querySelector("#audit-empty");
const emptyText = document.querySelector("#audit-empty-text");
const auditList = document.querySelector("#audit-list");
const resultsCount = document.querySelector("#audit-results-count");

const summaryElements = {
    total: document.querySelector("#audit-summary-total"),
    users: document.querySelector("#audit-summary-users"),
    resources: document.querySelector("#audit-summary-resources"),
    recent: document.querySelector("#audit-summary-recent"),
};

let auditLogs = [];

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

function formatDateTime(value) {
    if (!value) {
        return "Data não informada";
    }

    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
        return value;
    }

    return new Intl.DateTimeFormat("pt-BR", {
        dateStyle: "short",
        timeStyle: "medium",
    }).format(date);
}

function readableValue(value) {
    return String(value ?? "")
        .replace(/[._:-]+/g, " ")
        .replace(/\s+/g, " ")
        .trim();
}

function showMessage(text, type = "error") {
    pageMessage.textContent = text;
    pageMessage.className = `form-message form-message--page form-message--visible form-message--${type}`;
}

function clearMessage() {
    pageMessage.textContent = "";
    pageMessage.className = "form-message form-message--page";
}

function updateSummary() {
    const users = new Set(auditLogs.map((item) => item.usuario_id));
    const resources = new Set(auditLogs.map((item) => item.recurso).filter(Boolean));
    const cutoff = Date.now() - (24 * 60 * 60 * 1000);
    const recent = auditLogs.filter((item) => {
        const timestamp = new Date(item.criado_em).getTime();
        return Number.isFinite(timestamp) && timestamp >= cutoff;
    }).length;

    summaryElements.total.textContent = auditLogs.length.toLocaleString("pt-BR");
    summaryElements.users.textContent = users.size.toLocaleString("pt-BR");
    summaryElements.resources.textContent = resources.size.toLocaleString("pt-BR");
    summaryElements.recent.textContent = recent.toLocaleString("pt-BR");
}

function setSelectOptions(select, values, firstLabel) {
    const currentValue = select.value;
    select.innerHTML = [
        `<option value="todos">${firstLabel}</option>`,
        ...values.map((value) => (
            `<option value="${escapeHtml(value)}">${escapeHtml(readableValue(value))}</option>`
        )),
    ].join("");

    if (values.includes(currentValue)) {
        select.value = currentValue;
    }
}

function updateFilterOptions() {
    const resources = [...new Set(
        auditLogs.map((item) => item.recurso).filter(Boolean),
    )].sort((first, second) => first.localeCompare(second, "pt-BR"));

    const actions = [...new Set(
        auditLogs.map((item) => item.acao).filter(Boolean),
    )].sort((first, second) => first.localeCompare(second, "pt-BR"));

    setSelectOptions(resourceFilter, resources, "Todos os recursos");
    setSelectOptions(actionFilter, actions, "Todas as ações");
}

function filteredLogs() {
    const query = normalizeText(searchInput.value);
    const resource = resourceFilter.value;
    const action = actionFilter.value;

    return auditLogs.filter((item) => {
        const matchesResource = resource === "todos" || item.recurso === resource;
        const matchesAction = action === "todos" || item.acao === action;
        const searchable = normalizeText([
            item.id,
            item.usuario_id,
            item.usuario,
            item.role,
            item.acao,
            item.recurso,
            item.recurso_id,
            item.request_id,
            ...(item.campos_alterados ?? []),
        ].join(" "));

        return matchesResource && matchesAction && searchable.includes(query);
    });
}

function renderFields(fields) {
    if (!Array.isArray(fields) || fields.length === 0) {
        return '<span class="audit-card__muted">Nenhum campo listado</span>';
    }

    return `
        <ul class="audit-fields" aria-label="Campos alterados">
            ${fields.map((field) => `<li>${escapeHtml(field)}</li>`).join("")}
        </ul>
    `;
}

function renderAudit() {
    const results = filteredLogs();
    const hasActiveFilters = Boolean(normalizeText(searchInput.value))
        || resourceFilter.value !== "todos"
        || actionFilter.value !== "todos";

    resultsCount.textContent = `${results.length.toLocaleString("pt-BR")} de ${auditLogs.length.toLocaleString("pt-BR")} registros`;
    clearFiltersButton.hidden = !hasActiveFilters;
    emptyState.hidden = results.length > 0;

    if (results.length === 0) {
        emptyText.textContent = auditLogs.length === 0
            ? "Ainda não há ações sensíveis registradas."
            : "Altere a busca ou os filtros para visualizar outros resultados.";
    }

    auditList.innerHTML = results.map((item) => `
        <article class="audit-card">
            <div class="audit-card__rail" aria-hidden="true"></div>
            <div class="audit-card__content">
                <div class="audit-card__header">
                    <div>
                        <span class="audit-card__id">Registro #${item.id}</span>
                        <h3>${escapeHtml(readableValue(item.acao))}</h3>
                    </div>
                    <span class="audit-badge">${escapeHtml(readableValue(item.recurso))}</span>
                </div>

                <dl class="audit-card__meta">
                    <div>
                        <dt>Ator</dt>
                        <dd>${escapeHtml(item.usuario)} <small>(${escapeHtml(item.role)})</small></dd>
                    </div>
                    <div>
                        <dt>Recurso</dt>
                        <dd>${escapeHtml(item.recurso)}${item.recurso_id ? ` #${escapeHtml(item.recurso_id)}` : ""}</dd>
                    </div>
                    <div>
                        <dt>Horário</dt>
                        <dd>${escapeHtml(formatDateTime(item.criado_em))}</dd>
                    </div>
                </dl>

                <div class="audit-card__details">
                    <div>
                        <span>Campos alterados</span>
                        ${renderFields(item.campos_alterados)}
                    </div>
                    <div>
                        <span>Request ID</span>
                        <code>${escapeHtml(item.request_id ?? "não disponível")}</code>
                    </div>
                </div>
            </div>
        </article>
    `).join("");
}

async function loadAudit() {
    clearMessage();
    loadingState.hidden = false;
    emptyState.hidden = true;
    auditList.setAttribute("aria-busy", "true");
    refreshButton.disabled = true;

    try {
        auditLogs = await getAuditLogs();
        updateSummary();
        updateFilterOptions();
        renderAudit();
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

        showMessage(error.message);
    } finally {
        loadingState.hidden = true;
        auditList.removeAttribute("aria-busy");
        refreshButton.disabled = false;
    }
}

async function initialize() {
    if (!(await restoreSession())) {
        goToLogin();
        return;
    }

    try {
        const currentUser = await getCurrentUser();
        if (!hasPermission(currentUser, Permissions.AUDITORIA_LER)) {
            goToDashboard();
            return;
        }

        roleBadge.textContent = currentUser.role === "admin"
            ? "Administrador"
            : "Cliente";
        applyNavigationPermissions(currentUser);
        await loadAudit();
    } catch (error) {
        if (error instanceof ApiError && error.status === 401) {
            clearToken();
            goToLogin();
            return;
        }

        loadingState.hidden = true;
        showMessage(error.message);
    }
}

logoutButton.addEventListener("click", async () => {
    await logout();
    goToLogin();
});

refreshButton.addEventListener("click", loadAudit);
searchInput.addEventListener("input", renderAudit);
resourceFilter.addEventListener("change", renderAudit);
actionFilter.addEventListener("change", renderAudit);
clearFiltersButton.addEventListener("click", () => {
    searchInput.value = "";
    resourceFilter.value = "todos";
    actionFilter.value = "todos";
    renderAudit();
    searchInput.focus();
});

initialize();
