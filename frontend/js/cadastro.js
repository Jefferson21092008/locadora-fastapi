import {
    ApiError,
    clearToken,
    createClient,
} from "/app/js/api.js";

const form = document.querySelector("#register-form");
const nameInput = document.querySelector("#register-name");
const userInput = document.querySelector("#register-user");
const emailInput = document.querySelector("#register-email");
const passwordInput = document.querySelector("#register-password");
const passwordConfirmationInput = document.querySelector("#register-password-confirmation");
const togglePasswordButton = document.querySelector("#toggle-register-password");
const submitButton = document.querySelector("#register-button");
const message = document.querySelector("#register-message");

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

function validateForm() {
    const name = nameInput.value.trim();
    const user = userInput.value.trim();
    const email = emailInput.value.trim();
    const password = passwordInput.value;
    const passwordConfirmation = passwordConfirmationInput.value;

    if (name.length < 2 || !/[A-Za-zÀ-ÖØ-öø-ÿ]/.test(name)) {
        showMessage("Informe um nome com pelo menos dois caracteres e uma letra.");
        markInvalid(nameInput);
        return null;
    }

    if (!/^[A-Za-z0-9_.-]{3,30}$/.test(user)) {
        showMessage("O usuário deve ter de 3 a 30 caracteres e usar apenas letras, números, ponto, hífen ou underline.");
        markInvalid(userInput);
        return null;
    }

    if (!emailInput.validity.valid) {
        showMessage("Informe um endereço de e-mail válido.");
        markInvalid(emailInput);
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

    return {
        nome: name,
        usuario: user,
        email,
        senha: password,
    };
}

function setLoading(isLoading) {
    submitButton.disabled = isLoading;
    submitButton.querySelector("span:first-child").textContent = isLoading
        ? "Criando conta..."
        : "Criar conta";
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

for (const input of [
    nameInput,
    userInput,
    emailInput,
    passwordInput,
    passwordConfirmationInput,
]) {
    input.addEventListener("input", () => {
        input.removeAttribute("aria-invalid");
        clearMessage();
    });
}

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearMessage();

    const clientData = validateForm();
    if (!clientData) {
        return;
    }

    setLoading(true);

    try {
        await createClient(clientData);
        clearToken();
        form.reset();
        showMessage("Conta criada com sucesso. Abrindo o login...", "success");
        window.setTimeout(() => window.location.assign("/app/"), 1000);
    } catch (error) {
        const duplicateData = error instanceof ApiError && error.status === 400;
        showMessage(
            duplicateData
                ? error.message
                : `Não foi possível criar a conta. ${error.message}`,
        );
    } finally {
        setLoading(false);
    }
});
