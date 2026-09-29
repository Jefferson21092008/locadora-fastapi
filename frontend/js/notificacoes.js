import {
    ApiError,
    Permissions,
    applyNavigationPermissions,
    clearToken,
    getCurrentUser,
    hasPermission,
    logout,
    markAllNotificationsRead,
    markNotificationRead,
    queryNotifications,
    restoreSession,
    syncNotifications,
} from "/app/js/api.js";

const roleBadge = document.querySelector("#current-role");
const logoutButton = document.querySelector("#logout-button");
const refreshButton = document.querySelector("#refresh-notifications-button");
const statusFilter = document.querySelector("#notification-status-filter");
const markAllButton = document.querySelector("#mark-all-notifications-read");
const message = document.querySelector("#notifications-message");
const loading = document.querySelector("#notifications-loading");
const empty = document.querySelector("#notifications-empty");
const list = document.querySelector("#notifications-list");
const resultsCount = document.querySelector("#notifications-results-count");
const previousButton = document.querySelector("#notifications-page-previous");
const nextButton = document.querySelector("#notifications-page-next");
const pageLabel = document.querySelector("#notifications-page-label");

const summary = {
    total: document.querySelector("#notifications-summary-total"),
    unread: document.querySelector("#notifications-summary-unread"),
    read: document.querySelector("#notifications-summary-read"),
};

let currentPage = 1;
let totalPages = 1;
const perPage = 20;

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

function formatDateTime(value) {
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) {
        return value || "Data não informada";
    }

    return new Intl.DateTimeFormat("pt-BR", {
        dateStyle: "short",
        timeStyle: "short",
    }).format(parsed);
}

function readableType(value) {
    return String(value ?? "")
        .replaceAll("_", " ")
        .replace(/^./, (letter) => letter.toUpperCase());
}

function showMessage(text, type = "error") {
    message.textContent = text;
    message.className = `form-message form-message--page form-message--visible form-message--${type}`;
}

function clearMessage() {
    message.textContent = "";
    message.className = "form-message form-message--page";
}

function render(data) {
    const items = data.items ?? [];
    const dataSummary = data.resumo ?? {};

    summary.total.textContent = Number(dataSummary.total ?? 0).toLocaleString("pt-BR");
    summary.unread.textContent = Number(dataSummary.nao_lidas ?? 0).toLocaleString("pt-BR");
    summary.read.textContent = Number(dataSummary.lidas ?? 0).toLocaleString("pt-BR");

    totalPages = Math.max(Number(data.total_paginas ?? 0), 1);
    currentPage = Math.min(currentPage, totalPages);
    pageLabel.textContent = `Página ${currentPage} de ${totalPages}`;
    previousButton.disabled = currentPage <= 1;
    nextButton.disabled = currentPage >= totalPages;
    markAllButton.disabled = Number(dataSummary.nao_lidas ?? 0) === 0;

    resultsCount.textContent = `${Number(data.total ?? 0).toLocaleString("pt-BR")} notificações neste filtro`;
    empty.hidden = items.length > 0;

    list.innerHTML = items.map((item) => `
        <article class="notification-card ${item.lida ? "notification-card--read" : "notification-card--unread"}">
            <div class="notification-card__topline">
                <span class="notification-type">${escapeHtml(readableType(item.tipo))}</span>
                <time datetime="${escapeHtml(item.criada_em)}">${escapeHtml(formatDateTime(item.criada_em))}</time>
            </div>
            <h3>${escapeHtml(item.titulo)}</h3>
            <p>${escapeHtml(item.mensagem)}</p>
            <div class="notification-card__footer">
                <span>${item.email_status === "enviado" ? "E-mail enviado" : item.lida ? "Lida" : "Não lida"}</span>
                ${item.lida ? "" : `<button class="text-button" type="button" data-notification-read="${item.id}">Marcar como lida</button>`}
            </div>
        </article>
    `).join("");
}

async function loadNotifications({ synchronize = false } = {}) {
    clearMessage();
    loading.hidden = false;
    list.setAttribute("aria-busy", "true");
    refreshButton.disabled = true;

    try {
        if (synchronize) {
            await syncNotifications();
        }

        const data = await queryNotifications(
            currentPage,
            perPage,
            statusFilter.value,
        );
        render(data);
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
        loading.hidden = true;
        list.removeAttribute("aria-busy");
        refreshButton.disabled = false;
    }
}

list.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-notification-read]");
    if (!button) {
        return;
    }

    button.disabled = true;
    try {
        await markNotificationRead(Number(button.dataset.notificationRead));
        await loadNotifications();
    } catch (error) {
        showMessage(error.message);
        button.disabled = false;
    }
});

markAllButton.addEventListener("click", async () => {
    markAllButton.disabled = true;
    try {
        await markAllNotificationsRead();
        showMessage("Todas as notificações foram marcadas como lidas.", "success");
        await loadNotifications();
    } catch (error) {
        showMessage(error.message);
        markAllButton.disabled = false;
    }
});

statusFilter.addEventListener("change", () => {
    currentPage = 1;
    loadNotifications();
});

previousButton.addEventListener("click", () => {
    if (currentPage > 1) {
        currentPage -= 1;
        loadNotifications();
    }
});

nextButton.addEventListener("click", () => {
    if (currentPage < totalPages) {
        currentPage += 1;
        loadNotifications();
    }
});

refreshButton.addEventListener("click", () => loadNotifications({ synchronize: true }));

logoutButton.addEventListener("click", async () => {
    await logout();
    goToLogin();
});

async function init() {
    if (!(await restoreSession())) {
        goToLogin();
        return;
    }

    try {
        const user = await getCurrentUser();
        if (!hasPermission(user, Permissions.NOTIFICACOES_LER)) {
            goToDashboard();
            return;
        }

        roleBadge.textContent = user.role === "admin" ? "Administrador" : "Cliente";
        applyNavigationPermissions(user);
        await loadNotifications({ synchronize: true });
    } catch (error) {
        if (error instanceof ApiError && error.status === 401) {
            clearToken();
            goToLogin();
            return;
        }

        showMessage(error.message);
    }
}

init();
