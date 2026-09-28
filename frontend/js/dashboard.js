import {
    ApiError,
    Permissions,
    applyNavigationPermissions,
    clearToken,
    getCurrentUser,
    getSystemStatus,
    restoreSession,
    hasPermission,
    logout,
    renameCurrentUser,
} from "/app/js/api.js";

const username = document.querySelector("#current-username");
const role = document.querySelector("#current-role");
const logoutButton = document.querySelector("#logout-button");
const refreshButton = document.querySelector("#refresh-button");
const message = document.querySelector("#dashboard-message");
const syncLabel = document.querySelector("#dashboard-sync-label");
const syncDot = document.querySelector("#dashboard-sync-dot");
const lastUpdated = document.querySelector("#dashboard-last-updated");
const metricCards = document.querySelectorAll("[data-metric-card]");

const renameUserButton = document.querySelector(
    "#rename-user-button",
);

const renameUserDialog = document.querySelector(
    "#rename-user-dialog",
);

const renameUserForm = document.querySelector(
    "#rename-user-form",
);

const newUsernameInput = document.querySelector(
    "#new-username",
);

const currentPasswordInput = document.querySelector(
    "#current-password",
);

const renameUserMessage = document.querySelector(
    "#rename-user-message",
);

const saveUsernameButton = document.querySelector(
    "#save-username-button",
);

const metrics = {
    clientes: document.querySelector("#metric-clientes"),
    veiculos: document.querySelector("#metric-veiculos"),
    alugueis: document.querySelector("#metric-alugueis"),
    manutencoes: document.querySelector("#metric-manutencoes"),
};

function goToLogin() {
    window.location.replace("/app/");
}

function showMessage(text, type = "error") {
    message.textContent = text;
    message.className = `form-message form-message--page form-message--visible form-message--${type}`;
}

function clearMessage() {
    message.textContent = "";
    message.className = "form-message form-message--page";
}

function showRenameMessage(
    text,
    type = "error",
) {
    renameUserMessage.textContent = text;
    renameUserMessage.className =
        `form-message form-message--visible form-message--${type}`;
}

function clearRenameMessage() {
    renameUserMessage.textContent = "";
    renameUserMessage.className =
        "form-message";
}

function closeRenameDialog() {
    renameUserDialog.close();
    renameUserForm.reset();
    clearRenameMessage();
}

function updateMetrics(status) {
    for (const [name, element] of Object.entries(metrics)) {
        element.textContent = Number(status[name] ?? 0).toLocaleString("pt-BR");
    }
}

function setDashboardLoading(isLoading) {
    refreshButton.disabled = isLoading;
    refreshButton.textContent = isLoading
        ? "Atualizando..."
        : "Atualizar dados";

    for (const card of metricCards) {
        card.classList.toggle("dashboard-metric-card--loading", isLoading);
        card.setAttribute("aria-busy", String(isLoading));
    }

    if (isLoading) {
        syncLabel.textContent = "Sincronizando";
        syncDot.className = "status-dot status-dot--loading";
    }
}

function markDashboardSynced() {
    const now = new Date();
    const time = new Intl.DateTimeFormat(
        "pt-BR",
        {
            hour: "2-digit",
            minute: "2-digit",
        },
    ).format(now);

    syncLabel.textContent = "Sincronizado";
    syncDot.className = "status-dot status-dot--online";
    lastUpdated.textContent = `Atualizado às ${time}`;
}

function markDashboardError() {
    syncLabel.textContent = "Falha na atualização";
    syncDot.className = "status-dot status-dot--error";

    if (!lastUpdated.textContent.startsWith("Atualizado")) {
        lastUpdated.textContent = "Dados ainda não sincronizados";
    }
}

async function loadDashboard() {
    if (!(await restoreSession())) {
        goToLogin();
        return;
    }

    clearMessage();
    setDashboardLoading(true);

    try {
        const [currentUser, status] = await Promise.all([
            getCurrentUser(),
            getSystemStatus(),
        ]);

        username.textContent = currentUser.usuario;
        role.textContent = currentUser.role === "admin" ? "Administrador" : "Cliente";
        renameUserButton.hidden = !hasPermission(
            currentUser,
            Permissions.CONTA_RENOMEAR,
        );
        applyNavigationPermissions(currentUser);
        updateMetrics(status);
        markDashboardSynced();
    } catch (error) {
        markDashboardError();

        if (error instanceof ApiError && error.status === 401) {
            clearToken();
            goToLogin();
            return;
        }

        showMessage(error.message);
    } finally {
        setDashboardLoading(false);
    }
}

renameUserButton.addEventListener(
    "click",
    () => {
        clearRenameMessage();
        renameUserForm.reset();
        renameUserDialog.showModal();
        newUsernameInput.focus();
    },
);

for (
    const button of document.querySelectorAll(
        "[data-close-rename-user]",
    )
) {
    button.addEventListener(
        "click",
        closeRenameDialog,
    );
}

renameUserForm.addEventListener(
    "submit",
    async (event) => {
        event.preventDefault();

        clearRenameMessage();

        const novoUsuario =
            newUsernameInput.value.trim();

        const senhaAtual =
            currentPasswordInput.value;

        saveUsernameButton.disabled = true;

        try {
            const usuarioAtualizado =
                await renameCurrentUser(
                    novoUsuario,
                    senhaAtual,
                );

            username.textContent =
                usuarioAtualizado.usuario;

            showRenameMessage(
                "Nome de usuário alterado com sucesso.",
                "success",
            );

            window.setTimeout(
                closeRenameDialog,
                900,
            );
        } catch (error) {
            if (
                error instanceof ApiError
                && error.status === 401
            ) {
                clearToken();
                goToLogin();
                return;
            }

            showRenameMessage(
                error.message,
            );
        } finally {
            saveUsernameButton.disabled = false;
        }
    },
);

logoutButton.addEventListener("click", async () => {
    await logout();
    goToLogin();
});

refreshButton.addEventListener("click", loadDashboard);

loadDashboard();
