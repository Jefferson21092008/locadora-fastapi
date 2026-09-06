const TOKEN_KEY = "locadora_access_token";

export class ApiError extends Error {
    constructor(message, status = 0, details = null) {
        super(message);
        this.name = "ApiError";
        this.status = status;
        this.details = details;
    }
}

export function getToken() {
    return sessionStorage.getItem(TOKEN_KEY);
}

export function saveToken(token) {
    sessionStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
    sessionStorage.removeItem(TOKEN_KEY);
}

function errorMessage(payload, fallback) {
    if (typeof payload?.detail === "string") {
        return payload.detail;
    }

    if (Array.isArray(payload?.detail)) {
        const messages = payload.detail
            .map((item) => item?.msg)
            .filter(Boolean);

        if (messages.length > 0) {
            return messages.join(" ");
        }
    }

    return fallback;
}

export async function apiRequest(path, options = {}) {
    const headers = new Headers(options.headers ?? {});
    const token = getToken();

    if (options.body && !headers.has("Content-Type")) {
        headers.set("Content-Type", "application/json");
    }

    if (token && !headers.has("Authorization")) {
        headers.set("Authorization", `Bearer ${token}`);
    }

    let response;

    try {
        response = await fetch(path, {
            ...options,
            headers,
        });
    } catch (error) {
        throw new ApiError(
            "Não foi possível conectar à API. Confirme se a FastAPI está em execução.",
            0,
            error,
        );
    }

    const contentType = response.headers.get("content-type") ?? "";
    const payload = contentType.includes("application/json")
        ? await response.json()
        : await response.text();

    if (!response.ok) {
        throw new ApiError(
            errorMessage(payload, `A API respondeu com o status ${response.status}.`),
            response.status,
            payload,
        );
    }

    return payload;
}

export async function login(usuario, senha) {
    return apiRequest("/auth/login", {
        method: "POST",
        body: JSON.stringify({ usuario, senha }),
    });
}

export function requestPasswordReset(usuario) {
    return apiRequest("/auth/esqueci-senha", {
        method: "POST",
        body: JSON.stringify({ usuario }),
    });
}

export function resetPassword(token, novaSenha) {
    return apiRequest("/auth/redefinir-senha", {
        method: "POST",
        body: JSON.stringify({
            token,
            nova_senha: novaSenha,
        }),
    });
}

export function createClient(data) {
    return apiRequest("/clientes", {
        method: "POST",
        body: JSON.stringify(data),
    });
}

export function getClients() {
    return apiRequest("/clientes");
}

export function deactivateClient(clientId) {
    return apiRequest(`/clientes/${clientId}/desativar`, {
        method: "PATCH",
    });
}

export function reactivateClient(clientId) {
    return apiRequest(`/clientes/${clientId}/reativar`, {
        method: "PATCH",
    });
}

export function getCurrentUser() {
    return apiRequest("/auth/me");
}

export function renameCurrentUser(
    novoUsuario,
    senhaAtual,
) {
    return apiRequest(
        "/auth/me/usuario",
        {
            method: "PATCH",
            body: JSON.stringify({
                novo_usuario: novoUsuario,
                senha_atual: senhaAtual,
            }),
        },
    );
}

export function getSystemStatus() {
    return apiRequest("/status");
}

export function getVehicles() {
    return apiRequest("/veiculos");
}

export function createVehicle(data) {
    return apiRequest("/veiculos", {
        method: "POST",
        body: JSON.stringify(data),
    });
}

export function updateVehicle(vehicleId, data) {
    return apiRequest(`/veiculos/${vehicleId}`, {
        method: "PATCH",
        body: JSON.stringify(data),
    });
}

export function deactivateVehicle(vehicleId) {
    return apiRequest(`/veiculos/${vehicleId}/desativar`, {
        method: "PATCH",
    });
}

export function reactivateVehicle(vehicleId) {
    return apiRequest(`/veiculos/${vehicleId}/reativar`, {
        method: "PATCH",
    });
}

export function getRentals() {
    return apiRequest("/alugueis");
}

export function getMyRentals() {
    return apiRequest("/alugueis/me");
}

export function createRental(data) {
    return apiRequest("/alugueis", {
        method: "POST",
        body: JSON.stringify(data),
    });
}

export function returnVehicle(vehicleId, data) {
    return apiRequest(`/alugueis/${vehicleId}/devolver`, {
        method: "PATCH",
        body: JSON.stringify(data),
    });
}

export function getMaintenances() {
    return apiRequest("/manutencoes");
}

export function createMaintenance(data) {
    return apiRequest("/manutencoes", {
        method: "POST",
        body: JSON.stringify(data),
    });
}

export function finishMaintenance(vehicleId, data) {
    return apiRequest(`/manutencoes/${vehicleId}/finalizar`, {
        method: "PATCH",
        body: JSON.stringify(data),
    });
}

export function getReportSummary() {
    return apiRequest("/relatorios/resumo");
}

export function getTopRentedVehicles(limit = 10) {
    return apiRequest(`/relatorios/veiculos-mais-alugados?limite=${limit}`);
}

export function getRevenueByType() {
    return apiRequest("/relatorios/faturamento-por-tipo");
}

export function getMaintenanceCostsReport() {
    return apiRequest("/relatorios/custos-manutencao");
}

export function getTopCustomers(limit = 10) {
    return apiRequest(`/relatorios/clientes-mais-alugam?limite=${limit}`);
}

export function getFinancialSummary() {
    return apiRequest("/relatorios/resumo-financeiro");
}

export function getVehicleResults() {
    return apiRequest("/relatorios/resultado-por-veiculo");
}
