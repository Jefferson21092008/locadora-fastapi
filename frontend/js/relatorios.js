import {
    ApiError,
    clearToken,
    getCurrentUser,
    getFinancialSummary,
    getMaintenanceCostsReport,
    getReportSummary,
    getRevenueByType,
    getToken,
    getTopCustomers,
    getTopRentedVehicles,
    getVehicleResults,
} from "/app/js/api.js";

const roleBadge = document.querySelector("#current-role");
const logoutButton = document.querySelector("#logout-button");
const refreshButton = document.querySelector("#refresh-reports-button");
const limitInput = document.querySelector("#report-limit");
const pageMessage = document.querySelector("#reports-message");
const loadingState = document.querySelector("#reports-loading");
const reportsContent = document.querySelector("#reports-content");
const revenueByTypeContainer = document.querySelector("#revenue-by-type");
const topVehiclesContainer = document.querySelector("#top-vehicles");
const topCustomersContainer = document.querySelector("#top-customers");
const maintenanceCostsContainer = document.querySelector("#maintenance-costs");
const vehicleSearchInput = document.querySelector("#report-vehicle-search");
const vehicleResultsBody = document.querySelector("#vehicle-results");
const vehicleResultsEmpty = document.querySelector("#vehicle-results-empty");
const resultCard = document.querySelector("#report-result-card");

const fields = {
    revenue: document.querySelector("#report-revenue"),
    maintenanceCost: document.querySelector("#report-maintenance-cost"),
    grossResult: document.querySelector("#report-gross-result"),
    activeClients: document.querySelector("#report-active-clients"),
    activeVehicles: document.querySelector("#report-active-vehicles"),
    activeRentals: document.querySelector("#report-active-rentals"),
    finishedRentals: document.querySelector("#report-finished-rentals"),
    totalCollected: document.querySelector("#report-total-collected"),
};

let vehicleResults = [];

function goToLogin() {
    window.location.replace("/app/");
}

function goToDashboard() {
    window.location.replace("/app/dashboard.html");
}

function normalizeText(value) {
    return String(value ?? "")
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .trim()
        .toLowerCase();
}

function escapeHtml(value) {
    const characters = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;",
    };

    return String(value ?? "").replace(/[&<>"']/g, (character) => characters[character]);
}

function formatCurrency(value) {
    return Number(value ?? 0).toLocaleString("pt-BR", {
        style: "currency",
        currency: "BRL",
    });
}

function formatNumber(value) {
    return Number(value ?? 0).toLocaleString("pt-BR");
}

function showMessage(text) {
    pageMessage.textContent = text;
    pageMessage.className = "form-message form-message--page form-message--visible form-message--error";
}

function clearMessage() {
    pageMessage.textContent = "";
    pageMessage.className = "form-message form-message--page";
}

function renderSummary(summary, financial) {
    fields.revenue.textContent = formatCurrency(financial.receita_alugueis);
    fields.maintenanceCost.textContent = formatCurrency(financial.custos_manutencao);
    fields.grossResult.textContent = formatCurrency(financial.resultado_bruto);
    fields.activeClients.textContent = formatNumber(summary.clientes_ativos);
    fields.activeVehicles.textContent = formatNumber(summary.veiculos_ativos);
    fields.activeRentals.textContent = formatNumber(summary.alugueis_ativos);
    fields.finishedRentals.textContent = formatNumber(summary.alugueis_finalizados);
    fields.totalCollected.textContent = formatCurrency(summary.total_arrecadado);

    resultCard.classList.toggle(
        "financial-card--negative",
        Number(financial.resultado_bruto) < 0,
    );
}

function renderRevenueByType(items) {
    if (items.length === 0) {
        revenueByTypeContainer.innerHTML = '<p class="report-empty">Ainda não há faturamento registrado.</p>';
        return;
    }

    const highestRevenue = Math.max(...items.map((item) => Number(item.faturamento)), 0);

    revenueByTypeContainer.innerHTML = items.map((item) => {
        const percentage = highestRevenue > 0
            ? Math.max((Number(item.faturamento) / highestRevenue) * 100, 2)
            : 0;

        return `
            <div class="report-bar-row">
                <div class="report-bar-row__label">
                    <span>${escapeHtml(item.tipo)}</span>
                    <strong>${escapeHtml(formatCurrency(item.faturamento))}</strong>
                </div>
                <div class="report-bar" aria-hidden="true">
                    <span style="width: ${percentage.toFixed(2)}%"></span>
                </div>
                <small>${formatNumber(item.total_alugueis)} ${item.total_alugueis === 1 ? "aluguel" : "aluguéis"}</small>
            </div>
        `;
    }).join("");
}

function renderTopVehicles(items) {
    if (items.length === 0) {
        topVehiclesContainer.innerHTML = '<li class="report-empty">Ainda não há aluguéis registrados.</li>';
        return;
    }

    topVehiclesContainer.innerHTML = items.map((vehicle, index) => `
        <li class="ranking-item">
            <span class="ranking-item__position">${index + 1}</span>
            <div class="ranking-item__identity">
                <strong>${escapeHtml(vehicle.modelo)}</strong>
                <small>${escapeHtml(vehicle.tipo)} · ID ${vehicle.id}</small>
            </div>
            <span class="ranking-item__value">${formatNumber(vehicle.total_alugueis)} ${vehicle.total_alugueis === 1 ? "aluguel" : "aluguéis"}</span>
        </li>
    `).join("");
}

function renderTopCustomers(items) {
    if (items.length === 0) {
        topCustomersContainer.innerHTML = '<li class="report-empty">Ainda não há clientes com aluguéis.</li>';
        return;
    }

    topCustomersContainer.innerHTML = items.map((customer, index) => `
        <li class="ranking-item">
            <span class="ranking-item__position">${index + 1}</span>
            <div class="ranking-item__identity">
                <strong>${escapeHtml(customer.cliente_nome)}</strong>
                <small>@${escapeHtml(customer.cliente_usuario)} · ID ${customer.cliente_id}</small>
            </div>
            <div class="ranking-item__metric">
                <span>${formatNumber(customer.total_alugueis)} ${customer.total_alugueis === 1 ? "aluguel" : "aluguéis"}</span>
                <strong>${escapeHtml(formatCurrency(customer.total_gasto))}</strong>
            </div>
        </li>
    `).join("");
}

function renderMaintenanceCosts(items) {
    if (items.length === 0) {
        maintenanceCostsContainer.innerHTML = '<p class="report-empty">Ainda não há custos de manutenção registrados.</p>';
        return;
    }

    maintenanceCostsContainer.innerHTML = items.map((vehicle) => `
        <article class="report-compact-item">
            <div>
                <strong>${escapeHtml(vehicle.modelo)}</strong>
                <small>${escapeHtml(vehicle.tipo)} · ID ${vehicle.id}</small>
            </div>
            <div class="report-compact-item__metric">
                <strong>${escapeHtml(formatCurrency(vehicle.custo_total))}</strong>
                <small>${formatNumber(vehicle.total_manutencoes)} manutenç${vehicle.total_manutencoes === 1 ? "ão" : "ões"}</small>
            </div>
        </article>
    `).join("");
}

function filteredVehicleResults() {
    const query = normalizeText(vehicleSearchInput.value);

    return vehicleResults.filter((vehicle) => normalizeText(
        `${vehicle.id} ${vehicle.tipo} ${vehicle.modelo}`,
    ).includes(query));
}

function renderVehicleResults() {
    const results = filteredVehicleResults();
    vehicleResultsEmpty.hidden = results.length > 0;

    vehicleResultsBody.innerHTML = results.map((vehicle) => {
        const negative = Number(vehicle.resultado_bruto) < 0;

        return `
            <tr>
                <th scope="row">
                    <strong>${escapeHtml(vehicle.modelo)}</strong>
                    <small>${escapeHtml(vehicle.tipo)} · ID ${vehicle.id}</small>
                </th>
                <td>${formatNumber(vehicle.total_alugueis)}</td>
                <td>${escapeHtml(formatCurrency(vehicle.receita))}</td>
                <td>${formatNumber(vehicle.total_manutencoes)}</td>
                <td>${escapeHtml(formatCurrency(vehicle.custo_manutencao))}</td>
                <td class="report-table__result ${negative ? "report-table__result--negative" : ""}">
                    ${escapeHtml(formatCurrency(vehicle.resultado_bruto))}
                </td>
            </tr>
        `;
    }).join("");
}

async function loadReports() {
    clearMessage();
    loadingState.hidden = false;
    reportsContent.hidden = true;
    refreshButton.disabled = true;
    limitInput.disabled = true;

    try {
        const limit = Number(limitInput.value);
        const [
            summary,
            topVehicles,
            revenueByType,
            maintenanceCosts,
            topCustomers,
            financial,
            results,
        ] = await Promise.all([
            getReportSummary(),
            getTopRentedVehicles(limit),
            getRevenueByType(),
            getMaintenanceCostsReport(),
            getTopCustomers(limit),
            getFinancialSummary(),
            getVehicleResults(),
        ]);

        vehicleResults = results;
        renderSummary(summary, financial);
        renderRevenueByType(revenueByType);
        renderTopVehicles(topVehicles);
        renderTopCustomers(topCustomers);
        renderMaintenanceCosts(maintenanceCosts);
        renderVehicleResults();
        reportsContent.hidden = false;
    } catch (error) {
        if (error instanceof ApiError && error.status === 401) {
            clearToken();
            goToLogin();
            return;
        }

        if (error instanceof ApiError && error.status === 403) {
            goToDashboard();
            return;
        }

        showMessage(error.message);
    } finally {
        loadingState.hidden = true;
        refreshButton.disabled = false;
        limitInput.disabled = false;
    }
}

async function initialize() {
    if (!getToken()) {
        goToLogin();
        return;
    }

    try {
        const currentUser = await getCurrentUser();
        if (currentUser.role !== "admin") {
            goToDashboard();
            return;
        }

        roleBadge.textContent = "Administrador";
        await loadReports();
    } catch (error) {
        if (error instanceof ApiError && error.status === 401) {
            clearToken();
            goToLogin();
            return;
        }

        loadingState.hidden = true;
        showMessage(error.message);
    }
}

logoutButton.addEventListener("click", () => {
    clearToken();
    goToLogin();
});

refreshButton.addEventListener("click", loadReports);
limitInput.addEventListener("change", loadReports);
vehicleSearchInput.addEventListener("input", renderVehicleResults);

initialize();
