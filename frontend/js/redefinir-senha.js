import {
    ApiError,
    resetPassword,
} from "/app/js/api.js";

const form = document.querySelector("#reset-password-form");
const tokenInput = document.querySelector("#recovery-token");
const passwordInput = document.querySelector("#new-password");
const passwordConfirmationInput = document.querySelector("#new-password-confirmation");
const togglePasswordButton = document.querySelector("#toggle-new-password");
const submitButton = document.querySelector("#reset-password-button");
const message = document.querySelector("#reset-password-message");

function showMessage(text, type = "error") {
    message.textContent = text;
    message.className = `form-message form-message--visible form-message--${type}`;
}

function clearMessage() {
    message.textContent = "";
    message.className = "form-message";
}

function markInvalid(input) {
    input.setAttribute("aria-invalid", "true");
    input.focus();
}

function setLoading(isLoading) {
    submitButton.disabled = isLoading;
    submitButton.querySelector("span:first-child").textContent = isLoading
        ? "Redefinindo..."
        : "Redefinir senha";
}

function validateForm() {
    const token = tokenInput.value.trim();
    const password = passwordInput.value;
    const passwordConfirmation = passwordConfirmationInput.value;

    if (!token) {
        showMessage("Informe o token recebido por e-mail.");
        markInvalid(tokenInput);
        return null;
    }

    if (password.length < 8 || !/[A-Za-zÀ-ÖØ-öø-ÿ]/.test(password) || !/\d/.test(password)) {
        showMessage("A senha deve ter pelo menos oito caracteres, uma letra e um número.");
        markInvalid(passwordInput);
        return null;
    }

    if (password !== passwordConfirmation) {
        showMessage("As senhas informadas não são iguais.");
        markInvalid(passwordConfirmationInput);
        return null;
    }

    return { token, password };
}

togglePasswordButton.addEventListener("click", () => {
    const showingPassword = passwordInput.type === "text";
    const newType = showingPassword ? "password" : "text";

    passwordInput.type = newType;
    passwordConfirmationInput.type = newType;
    togglePasswordButton.textContent = showingPassword ? "Mostrar" : "Ocultar";
    togglePasswordButton.setAttribute("aria-pressed", String(!showingPassword));
    passwordInput.focus();
});

for (const input of [tokenInput, passwordInput, passwordConfirmationInput]) {
    input.addEventListener("input", () => {
        input.removeAttribute("aria-invalid");
        clearMessage();
    });
}

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearMessage();

    const data = validateForm();
    if (!data) {
        return;
    }

    setLoading(true);

    try {
        const response = await resetPassword(data.token, data.password);
        form.reset();
        showMessage(`${response.mensagem} Abrindo o login...`, "success");
        window.setTimeout(() => window.location.assign("/app/"), 1200);
    } catch (error) {
        const invalidToken = error instanceof ApiError && error.status === 400;
        showMessage(
            invalidToken
                ? error.message
                : error instanceof ApiError
                    ? `Não foi possível redefinir a senha. ${error.message}`
                    : "Não foi possível redefinir a senha. Tente novamente.",
        );
    } finally {
        setLoading(false);
    }
});

const tokenFromUrl = new URLSearchParams(window.location.search).get("token");
if (tokenFromUrl) {
    tokenInput.value = tokenFromUrl.trim();
    passwordInput.focus();
}
