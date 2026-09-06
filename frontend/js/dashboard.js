import {
    ApiError,
    clearToken,
    getCurrentUser,
    getSystemStatus,
    getToken,
    renameCurrentUser,
} from "/app/js/api.js";

const username = document.querySelector("#current-username");
const role = document.querySelector("#current-role");
const logoutButton = document.querySelector("#logout-button");
const refreshButton = document.querySelector("#refresh-button");
const message = document.querySelector("#dashboard-message");

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
        renameUserButton.hidden =
            currentUser.role !== "cliente";
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

logoutButton.addEventListener("click", () => {
    clearToken();
    goToLogin();
});

refreshButton.addEventListener("click", loadDashboard);

loadDashboard();
