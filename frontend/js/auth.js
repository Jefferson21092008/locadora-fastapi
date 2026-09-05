import {
    ApiError,
    clearToken,
    getCurrentUser,
    getToken,
    login,
    saveToken,
} from "/app/js/api.js";

const form = document.querySelector("#login-form");
const userInput = document.querySelector("#usuario");
const passwordInput = document.querySelector("#senha");
const submitButton = document.querySelector("#login-button");
const togglePasswordButton = document.querySelector("#toggle-password");
const message = document.querySelector("#login-message");

function showMessage(text, type = "error") {
    message.textContent = text;
    message.className = `form-message form-message--visible form-message--${type}`;
}

function clearMessage() {
    message.textContent = "";
    message.className = "form-message";
}

function setLoading(isLoading) {
    submitButton.disabled = isLoading;
    submitButton.querySelector("span:first-child").textContent = isLoading
        ? "Entrando..."
        : "Entrar";
}

function validateForm() {
    const usuario = userInput.value.trim();
    const senha = passwordInput.value;

    userInput.setAttribute("aria-invalid", String(usuario.length === 0));
    passwordInput.setAttribute("aria-invalid", String(senha.length === 0));

    if (!usuario || !senha) {
        showMessage("Preencha o usuário e a senha para continuar.");
        (!usuario ? userInput : passwordInput).focus();
        return null;
    }

    return { usuario, senha };
}

async function redirectAuthenticatedUser() {
    if (!getToken()) {
        return;
    }

    try {
        await getCurrentUser();
        window.location.replace("/app/dashboard.html");
    } catch {
        clearToken();
    }
}

togglePasswordButton.addEventListener("click", () => {
    const showingPassword = passwordInput.type === "text";
    passwordInput.type = showingPassword ? "password" : "text";
    togglePasswordButton.textContent = showingPassword ? "Mostrar" : "Ocultar";
    togglePasswordButton.setAttribute("aria-pressed", String(!showingPassword));
    passwordInput.focus();
});

for (const input of [userInput, passwordInput]) {
    input.addEventListener("input", () => {
        input.removeAttribute("aria-invalid");
        clearMessage();
    });
}

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearMessage();

    const credentials = validateForm();
    if (!credentials) {
        return;
    }

    setLoading(true);

    try {
        const response = await login(credentials.usuario, credentials.senha);
        saveToken(response.access_token);
        showMessage("Login realizado. Abrindo o painel...", "success");
        window.location.assign("/app/dashboard.html");
    } catch (error) {
        const invalidCredentials = error instanceof ApiError && error.status === 401;
        showMessage(
            invalidCredentials
                ? "Usuário ou senha incorretos. Confira os dados e tente novamente."
                : error.message,
        );
        passwordInput.select();
    } finally {
        setLoading(false);
    }
});

redirectAuthenticatedUser();
