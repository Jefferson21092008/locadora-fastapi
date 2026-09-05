import {
    ApiError,
    requestPasswordReset,
} from "/app/js/api.js";

const form = document.querySelector("#forgot-password-form");
const userInput = document.querySelector("#recovery-user");
const submitButton = document.querySelector("#forgot-password-button");
const message = document.querySelector("#forgot-password-message");

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
        ? "Enviando..."
        : "Enviar instruções";
}

userInput.addEventListener("input", () => {
    userInput.removeAttribute("aria-invalid");
    clearMessage();
});

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearMessage();

    const user = userInput.value.trim();
    if (!user) {
        userInput.setAttribute("aria-invalid", "true");
        showMessage("Informe seu nome de usuário para continuar.");
        userInput.focus();
        return;
    }

    setLoading(true);

    try {
        const response = await requestPasswordReset(user);
        form.reset();
        showMessage(response.mensagem, "success");
    } catch (error) {
        showMessage(
            error instanceof ApiError
                ? error.message
                : "Não foi possível solicitar a recuperação. Tente novamente.",
        );
    } finally {
        setLoading(false);
    }
});
