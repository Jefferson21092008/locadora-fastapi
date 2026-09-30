import {
    ApiError,
    Permissions,
    applyNavigationPermissions,
    clearToken,
    getCurrentUser,
    getDashboardMetrics,
    getSystemStatus,
    restoreSession,
    syncNotifications,
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
const metricCaptions = {
    clientes: document.querySelector("#metric-clientes-caption"),
    veiculos: document.querySelector("#metric-veiculos-caption"),
    alugueis: document.querySelector("#metric-alugueis-caption"),
    manutencoes: document.querySelector("#metric-manutencoes-caption"),
};

const adminInsights = document.querySelector(
    "#admin-dashboard-insights",
);
const dashboardEndpoint = document.querySelector(
    "#dashboard-endpoint",
);
const vehiclesAvailable = document.querySelector(
    "#dashboard-vehicles-available",
);
const vehiclesRented = document.querySelector(
    "#dashboard-vehicles-rented",
);
const vehiclesMaintenance = document.querySelector(
    "#dashboard-vehicles-maintenance",
);
const fleetRate = document.querySelector(
    "#dashboard-fleet-rate",
);
const revenue = document.querySelector("#dashboard-revenue");
const maintenanceCost = document.querySelector(
    "#dashboard-maintenance-cost",
);
const grossResult = document.querySelector(
    "#dashboard-gross-result",
);
const resultCard = document.querySelector(
    "#dashboard-result-card",
);
const finishedRentals = document.querySelector(
    "#dashboard-finished-rentals",
);
const finishedMaintenance = document.querySelector(
    "#dashboard-finished-maintenance",
);
const averageTicket = document.querySelector(
    "#dashboard-average-ticket",
);

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

function formatNumber(value) {
    return Number(value ?? 0).toLocaleString("pt-BR");
}

function formatCurrency(value) {
    return new Intl.NumberFormat(
        "pt-BR",
        {
            style: "currency",
            currency: "BRL",
        },
    ).format(Number(value ?? 0));
}

function updateBasicMetrics(status) {
    for (const [name, element] of Object.entries(metrics)) {
        element.textContent = formatNumber(status[name]);
    }

    metricCaptions.clientes.textContent = "cadastrados";
    metricCaptions.veiculos.textContent = "na frota";
    metricCaptions.alugueis.textContent = "registrados";
    metricCaptions.manutencoes.textContent = "registradas";
    dashboardEndpoint.textContent = "/api/v1/status";
    adminInsights.hidden = true;
}

function updateAdminMetrics(data) {
    metrics.clientes.textContent = formatNumber(data.clientes_ativos);
    metrics.veiculos.textContent = formatNumber(data.veiculos_disponiveis);
    metrics.alugueis.textContent = formatNumber(data.alugueis_ativos);
    metrics.manutencoes.textContent = formatNumber(data.manutencoes_ativas);

    metricCaptions.clientes.textContent =
        `ativos • ${formatNumber(data.clientes_inativos)} inativos`;
    metricCaptions.veiculos.textContent =
        `disponíveis • ${formatNumber(data.veiculos_desativados)} desativados`;
    metricCaptions.alugueis.textContent =
        `ativos • ${formatNumber(data.alugueis_finalizados)} finalizados`;
    metricCaptions.manutencoes.textContent =
        `ativas • ${formatNumber(data.manutencoes_finalizadas)} finalizadas`;

    vehiclesAvailable.textContent = formatNumber(data.veiculos_disponiveis);
    vehiclesRented.textContent = formatNumber(data.veiculos_alugados);
    vehiclesMaintenance.textContent = formatNumber(data.veiculos_manutencao);
    fleetRate.textContent = `${formatNumber(data.taxa_frota_alugada)}%`;

    revenue.textContent = formatCurrency(data.receita_alugueis);
    maintenanceCost.textContent = formatCurrency(data.custos_manutencao);
    grossResult.textContent = formatCurrency(data.resultado_bruto);
    finishedRentals.textContent =
        `aluguéis finalizados: ${formatNumber(data.alugueis_finalizados)}`;
    finishedMaintenance.textContent =
        `manutenções finalizadas: ${formatNumber(data.manutencoes_finalizadas)}`;
    averageTicket.textContent =
        `ticket médio: ${formatCurrency(data.ticket_medio)}`;

    resultCard.classList.toggle(
        "financial-card--negative",
        Number(data.resultado_bruto) < 0,
    );
    dashboardEndpoint.textContent = "/api/v1/relatorios/dashboard";
    adminInsights.hidden = false;
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

async function loadDashboard(forcarAtualizacao = false) {
    if (!(await restoreSession())) {
        goToLogin();
        return;
    }

    clearMessage();
    setDashboardLoading(true);

    try {
        const currentUser = await getCurrentUser();
        const canViewReports = hasPermission(
            currentUser,
            Permissions.RELATORIOS_LER,
        );
        const dashboardData = canViewReports
            ? await getDashboardMetrics(forcarAtualizacao)
            : await getSystemStatus();

        username.textContent = currentUser.usuario;
        role.textContent = currentUser.role === "admin" ? "Administrador" : "Cliente";
        renameUserButton.hidden = !hasPermission(
            currentUser,
            Permissions.CONTA_RENOMEAR,
        );
        applyNavigationPermissions(currentUser);

        if (canViewReports) {
            updateAdminMetrics(dashboardData);
        } else {
            updateBasicMetrics(dashboardData);
        }

        syncNotifications().catch(() => {});
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

refreshButton.addEventListener(
    "click",
    () => loadDashboard(true),
);

loadDashboard();
