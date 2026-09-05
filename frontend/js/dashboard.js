import {
    ApiError,
    clearToken,
    getCurrentUser,
    getSystemStatus,
    getToken,
} from "/app/js/api.js";

const username = document.querySelector("#current-username");
const role = document.querySelector("#current-role");
const logoutButton = document.querySelector("#logout-button");
const refreshButton = document.querySelector("#refresh-button");
const message = document.querySelector("#dashboard-message");

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

function updateMetrics(status) {
    for (const [name, element] of Object.entries(metrics)) {
        element.textContent = Number(status[name] ?? 0).toLocaleString("pt-BR");
    }
}

async function loadDashboard() {
    if (!getToken()) {
        goToLogin();
        return;
    }

    clearMessage();
    refreshButton.disabled = true;
    refreshButton.textContent = "Atualizando...";

    try {
        const [currentUser, status] = await Promise.all([
            getCurrentUser(),
            getSystemStatus(),
        ]);

        username.textContent = currentUser.usuario;
        role.textContent = currentUser.role === "admin" ? "Administrador" : "Cliente";
        for (const link of document.querySelectorAll(".admin-nav")) {
            link.hidden = currentUser.role !== "admin";
        }
        updateMetrics(status);
    } catch (error) {
        if (error instanceof ApiError && error.status === 401) {
            clearToken();
            goToLogin();
            return;
        }

        showMessage(error.message);
    } finally {
        refreshButton.disabled = false;
        refreshButton.textContent = "Atualizar dados";
    }
}

logoutButton.addEventListener("click", () => {
    clearToken();
    goToLogin();
});

refreshButton.addEventListener("click", loadDashboard);

loadDashboard();
