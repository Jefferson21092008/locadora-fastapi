const API_BASE = "/api/v1";

let accessToken = null;
let refreshPromise = null;

export const Permissions = Object.freeze({
    CLIENTES_LER: "clientes:ler",
    CLIENTES_GERENCIAR_STATUS: "clientes:gerenciar_status",
    VEICULOS_CRIAR: "veiculos:criar",
    VEICULOS_EDITAR: "veiculos:editar",
    VEICULOS_GERENCIAR_STATUS: "veiculos:gerenciar_status",
    ALUGUEIS_LER: "alugueis:ler",
    ALUGUEIS_CRIAR: "alugueis:criar",
    ALUGUEIS_PROPRIOS_LER: "alugueis:proprios:ler",
    ALUGUEIS_DEVOLVER: "alugueis:devolver",
    MANUTENCOES_LER: "manutencoes:ler",
    MANUTENCOES_CRIAR: "manutencoes:criar",
    MANUTENCOES_EDITAR: "manutencoes:editar",
    MANUTENCOES_FINALIZAR: "manutencoes:finalizar",
    RELATORIOS_LER: "relatorios:ler",
    AUDITORIA_LER: "auditoria:ler",
    CONTA_RENOMEAR: "conta:renomear",
    SESSOES_GERENCIAR: "sessoes:gerenciar",
});

export function hasPermission(user, permission) {
    return Array.isArray(user?.permissoes)
        && user.permissoes.includes(permission);
}

const NAVIGATION_PERMISSIONS = Object.freeze({
    "/app/clientes.html": Permissions.CLIENTES_LER,
    "/app/manutencoes.html": Permissions.MANUTENCOES_LER,
    "/app/relatorios.html": Permissions.RELATORIOS_LER,
    "/app/auditoria.html": Permissions.AUDITORIA_LER,
});

export function applyNavigationPermissions(user, root = document) {
    for (const link of root.querySelectorAll(".admin-nav")) {
        const permission = NAVIGATION_PERMISSIONS[link.getAttribute("href")];
        link.hidden = !permission || !hasPermission(user, permission);
    }
}

export class ApiError extends Error {
    constructor(message, status = 0, details = null) {
        super(message);
        this.name = "ApiError";
        this.status = status;
        this.details = details;
    }
}

function getToken() {
    return accessToken;
}

function saveToken(token) {
    accessToken = token;
}

export function clearToken() {
    accessToken = null;
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

async function readPayload(response) {
    const contentType = response.headers.get("content-type") ?? "";
    return contentType.includes("application/json")
        ? response.json()
        : response.text();
}

async function requestRefreshToken() {
    let response;

    try {
        response = await fetch(`${API_BASE}/auth/refresh`, {
            method: "POST",
            credentials: "same-origin",
        });
    } catch (error) {
        clearToken();
        throw new ApiError(
            "Não foi possível renovar a sessão.",
            0,
            error,
        );
    }

    const payload = await readPayload(response);

    if (!response.ok) {
        clearToken();
        throw new ApiError(
            errorMessage(payload, "A sessão expirou. Faça login novamente."),
            response.status,
            payload,
        );
    }

    saveToken(payload.access_token);
    return payload.access_token;
}

async function performRefresh() {
    if (navigator.locks?.request) {
        return navigator.locks.request(
            "locadora-refresh-token",
            requestRefreshToken,
        );
    }

    return requestRefreshToken();
}

export async function refreshSession() {
    if (!refreshPromise) {
        refreshPromise = performRefresh();
    }

    try {
        return await refreshPromise;
    } finally {
        refreshPromise = null;
    }
}

export async function restoreSession() {
    if (getToken()) {
        return true;
    }

    try {
        await refreshSession();
        return true;
    } catch {
        return false;
    }
}

export async function apiRequest(path, options = {}, allowRefresh = true) {
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
        response = await fetch(`${API_BASE}${path}`, {
            ...options,
            credentials: "same-origin",
            headers,
        });
    } catch (error) {
        throw new ApiError(
            "Não foi possível conectar à API. Confirme se a FastAPI está em execução.",
            0,
            error,
        );
    }

    if (
        response.status === 401
        && allowRefresh
        && path !== "/auth/login"
        && path !== "/auth/refresh"
    ) {
        try {
            await refreshSession();
            return apiRequest(path, options, false);
        } catch {
            clearToken();
        }
    }

    const payload = await readPayload(response);

    if (!response.ok) {
        throw new ApiError(
            errorMessage(payload, `A API respondeu com o status ${response.status}.`),
            response.status,
            payload,
        );
    }

    return payload;
}

function filenameFromContentDisposition(value) {
    if (!value) {
        return null;
    }

    const match = value.match(/filename="?([^";]+)"?/i);
    return match?.[1] ?? null;
}

export async function apiDownload(path, allowRefresh = true) {
    const headers = new Headers();
    const token = getToken();

    if (token) {
        headers.set("Authorization", `Bearer ${token}`);
    }

    let response;

    try {
        response = await fetch(`${API_BASE}${path}`, {
            method: "GET",
            credentials: "same-origin",
            headers,
        });
    } catch (error) {
        throw new ApiError(
            "Não foi possível conectar à API para gerar o arquivo.",
            0,
            error,
        );
    }

    if (
        response.status === 401
        && allowRefresh
    ) {
        try {
            await refreshSession();
            return apiDownload(path, false);
        } catch {
            clearToken();
        }
    }

    if (!response.ok) {
        const payload = await readPayload(response);

        throw new ApiError(
            errorMessage(
                payload,
                `A API respondeu com o status ${response.status}.`,
            ),
            response.status,
            payload,
        );
    }

    return {
        blob: await response.blob(),
        filename: (
            filenameFromContentDisposition(
                response.headers.get("content-disposition"),
            )
            ?? "relatorio"
        ),
    };
}


function buildQuery(params = {}) {
    const query = new URLSearchParams();

    for (const [key, value] of Object.entries(params)) {
        if (value === undefined || value === null || value === "") {
            continue;
        }

        query.set(key, String(value));
    }

    const serialized = query.toString();
    return serialized ? `?${serialized}` : "";
}

export async function logout() {
    try {
        await fetch(`${API_BASE}/auth/logout`, {
            method: "POST",
            credentials: "same-origin",
        });
    } finally {
        clearToken();
    }
}

export async function login(usuario, senha) {
    const payload = await apiRequest("/auth/login", {
        method: "POST",
        body: JSON.stringify({ usuario, senha }),
    });

    saveToken(payload.access_token);
    return payload;
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

export function queryClients(params = {}) {
    return apiRequest(`/clientes/consulta${buildQuery(params)}`);
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

export function getSessions() {
    return apiRequest("/auth/sessoes");
}

export function revokeSession(sessionId) {
    return apiRequest(`/auth/sessoes/${sessionId}`, {
        method: "DELETE",
    });
}

export function revokeAllSessions() {
    return apiRequest("/auth/sessoes", {
        method: "DELETE",
    });
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

export function queryVehicles(params = {}) {
    return apiRequest(`/veiculos/consulta${buildQuery(params)}`);
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

export function queryRentals(params = {}, own = false) {
    const path = own ? "/alugueis/me/consulta" : "/alugueis/consulta";
    return apiRequest(`${path}${buildQuery(params)}`);
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

export function queryMaintenances(params = {}) {
    return apiRequest(`/manutencoes/consulta${buildQuery(params)}`);
}

export function createMaintenance(data) {
    return apiRequest("/manutencoes", {
        method: "POST",
        body: JSON.stringify(data),
    });
}

export function updateMaintenance(maintenanceId, data) {
    return apiRequest(`/manutencoes/${maintenanceId}`, {
        method: "PATCH",
        body: JSON.stringify(data),
    });
}

export function finishMaintenance(vehicleId, data) {
    return apiRequest(`/manutencoes/${vehicleId}/finalizar`, {
        method: "PATCH",
        body: JSON.stringify(data),
    });
}

export function getDashboardMetrics() {
    return apiRequest("/relatorios/dashboard");
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

export function getAuditLogs() {
    return apiRequest("/auditoria");
}

export function getVehicleResults() {
    return apiRequest("/relatorios/resultado-por-veiculo");
}


export function downloadVehicleResultReport(format) {
    return apiDownload(
        `/relatorios/resultado-por-veiculo/exportar/${format}`,
    );
}
