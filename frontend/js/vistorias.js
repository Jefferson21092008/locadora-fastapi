import {
    ApiError,
    Permissions,
    applyNavigationPermissions,
    cancelDamage,
    cancelTrafficFine,
    clearToken,
    createDamage,
    createInspection,
    createTrafficFine,
    getCurrentUser,
    getInspectionSummary,
    getRentals,
    hasPermission,
    logout,
    restoreSession,
    saveDeposit,
} from "/app/js/api.js";

const roleBadge = document.querySelector("#current-role");
const logoutButton = document.querySelector("#logout-button");
const pageMessage = document.querySelector("#inspection-message");
const rentalSelect = document.querySelector("#inspection-rental");
const refreshButton = document.querySelector("#refresh-inspection-button");
const emptyState = document.querySelector("#inspection-empty");
const content = document.querySelector("#inspection-content");
const rentalSummary = document.querySelector("#inspection-rental-summary");

const fuelStart = document.querySelector("#inspection-fuel-start");
const fuelEnd = document.querySelector("#inspection-fuel-end");
const fuelMissing = document.querySelector("#inspection-fuel-missing");
const pendingTotal = document.querySelector("#inspection-pending-total");

const inspectionForm = document.querySelector("#inspection-form");
const inspectionType = document.querySelector("#inspection-type");
const inspectionOdometer = document.querySelector("#inspection-odometer");
const inspectionFuel = document.querySelector("#inspection-fuel");
const inspectionNotes = document.querySelector("#inspection-notes");
const inspectionRecords = document.querySelector("#inspection-records");

const damageForm = document.querySelector("#damage-form");
const damageDescription = document.querySelector("#damage-description");
const damageValue = document.querySelector("#damage-value");
const damageRecords = document.querySelector("#damage-records");

const trafficFineForm = document.querySelector("#traffic-fine-form");
const trafficFineDescription = document.querySelector("#traffic-fine-description");
const trafficFineValue = document.querySelector("#traffic-fine-value");
const trafficFineDate = document.querySelector("#traffic-fine-date");
const trafficFineRecords = document.querySelector("#traffic-fine-records");

const depositForm = document.querySelector("#deposit-form");
const depositValue = document.querySelector("#deposit-value");
const depositReleased = document.querySelector("#deposit-released");
const depositNotes = document.querySelector("#deposit-notes");
const depositRecord = document.querySelector("#deposit-record");

let currentUser = null;
let rentals = [];
let summary = null;

function goToLogin() {
    window.location.replace("/app/");
}

function can(permission) {
    return hasPermission(
        currentUser,
        permission,
    );
}

function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function formatCurrency(value) {
    return Number(
        value ?? 0
    ).toLocaleString(
        "pt-BR",
        {
            style: "currency",
            currency: "BRL",
        },
    );
}

function formatNumber(value) {
    return Number(
        value ?? 0
    ).toLocaleString(
        "pt-BR",
        {
            maximumFractionDigits: 1,
        },
    );
}

function todayIsoDate() {
    const today = new Date();
    const year = today.getFullYear();
    const month = String(
        today.getMonth() + 1
    ).padStart(2, "0");
    const day = String(
        today.getDate()
    ).padStart(2, "0");

    return `${year}-${month}-${day}`;
}

function formatDate(value) {
    if (!value) {
        return "—";
    }

    const raw = String(value).slice(0, 10);
    const [year, month, day] = raw.split("-");

    if (!year || !month || !day) {
        return escapeHtml(value);
    }

    return `${day}/${month}/${year}`;
}

function showMessage(
    element,
    text,
    type = "error",
) {
    element.textContent = text;
    element.dataset.type = type;
}

function clearMessage(
    element,
) {
    element.textContent = "";
    delete element.dataset.type;
}

function selectedRentalId() {
    const id = Number(
        rentalSelect.value
    );

    return Number.isInteger(id)
        && id > 0
        ? id
        : null;
}

function populateRentals() {
    const previous = rentalSelect.value;

    rentalSelect.innerHTML = `
        <option value="">Selecione um aluguel</option>
        ${rentals
            .slice()
            .sort((first, second) => second.id - first.id)
            .map((rental) => `
                <option value="${rental.id}">
                    #${rental.id} · ${escapeHtml(rental.veiculo_modelo)} · ${escapeHtml(rental.cliente_nome)} · ${rental.status === "ativo" ? "ativo" : "finalizado"}
                </option>
            `)
            .join("")}
    `;

    if (
        previous
        && rentals.some(
            (rental) => String(rental.id) === previous,
        )
    ) {
        rentalSelect.value = previous;
    }

    const params = new URLSearchParams(
        window.location.search
    );
    const requested = params.get(
        "aluguel"
    );

    if (
        requested
        && rentals.some(
            (rental) => String(rental.id) === requested,
        )
    ) {
        rentalSelect.value = requested;
    }
}

function renderRentalSummary() {
    const rental = summary.aluguel;

    rentalSummary.innerHTML = `
        <div>
            <span>Aluguel</span>
            <strong>#${rental.id}</strong>
        </div>
        <div>
            <span>Veículo</span>
            <strong>${escapeHtml(rental.veiculo_modelo)}</strong>
            <small>${escapeHtml(rental.veiculo_tipo)} · ID ${rental.veiculo_id}</small>
        </div>
        <div>
            <span>Cliente</span>
            <strong>${escapeHtml(rental.cliente_nome)}</strong>
            <small>@${escapeHtml(rental.cliente_usuario)}</small>
        </div>
        <div>
            <span>Status</span>
            <strong>${rental.status === "ativo" ? "Ativo" : "Finalizado"}</strong>
            <small>${formatDate(rental.data_inicio)} → ${formatDate(rental.data_fim ?? rental.data_prevista)}</small>
        </div>
    `;
}

function renderIndicators() {
    const indicators = summary.indicadores;

    fuelStart.textContent = (
        indicators.combustivel_retirada === null
            ? "—"
            : `${indicators.combustivel_retirada}%`
    );
    fuelEnd.textContent = (
        indicators.combustivel_devolucao === null
            ? "—"
            : `${indicators.combustivel_devolucao}%`
    );
    fuelMissing.textContent = (
        `${indicators.combustivel_faltante}%`
    );
    pendingTotal.textContent = formatCurrency(
        indicators.pendencias_estimadas_total
    );
}

function renderInspections() {
    if (summary.inspecoes.length === 0) {
        inspectionRecords.innerHTML = `
            <p class="inspection-records__empty">Nenhuma inspeção registrada.</p>
        `;
        return;
    }

    inspectionRecords.innerHTML = summary.inspecoes.map((item) => `
        <article class="inspection-record">
            <div>
                <strong>${item.tipo === "retirada" ? "Retirada" : "Devolução"}</strong>
                <span>${formatNumber(item.quilometragem)} km · ${item.combustivel_percentual}% combustível</span>
            </div>
            <p>${escapeHtml(item.observacoes ?? "Sem observações.")}</p>
        </article>
    `).join("");
}

function renderDamages() {
    if (summary.danos.length === 0) {
        damageRecords.innerHTML = `
            <p class="inspection-records__empty">Nenhum dano registrado.</p>
        `;
        return;
    }

    damageRecords.innerHTML = summary.danos.map((item) => `
        <article class="inspection-record ${item.status === "cancelado" ? "inspection-record--muted" : ""}">
            <div>
                <strong>${escapeHtml(item.descricao)}</strong>
                <span>${formatCurrency(item.valor_estimado)} · ${item.status}</span>
            </div>
            ${item.status === "ativo" && can(Permissions.DANOS_GERENCIAR) ? `
                <button class="text-button" type="button" data-cancel-damage="${item.id}">
                    Cancelar registro
                </button>
            ` : ""}
        </article>
    `).join("");

    for (const button of damageRecords.querySelectorAll("[data-cancel-damage]")) {
        button.addEventListener(
            "click",
            handleCancelDamage,
        );
    }
}

function renderTrafficFines() {
    if (summary.multas.length === 0) {
        trafficFineRecords.innerHTML = `
            <p class="inspection-records__empty">Nenhuma multa de trânsito registrada.</p>
        `;
        return;
    }

    trafficFineRecords.innerHTML = summary.multas.map((item) => `
        <article class="inspection-record ${item.status === "cancelada" ? "inspection-record--muted" : ""}">
            <div>
                <strong>${escapeHtml(item.descricao)}</strong>
                <span>${formatCurrency(item.valor)} · ${formatDate(item.data_ocorrencia)} · ${item.status}</span>
            </div>
            ${item.status === "ativa" && can(Permissions.MULTAS_GERENCIAR) ? `
                <button class="text-button" type="button" data-cancel-fine="${item.id}">
                    Cancelar registro
                </button>
            ` : ""}
        </article>
    `).join("");

    for (const button of trafficFineRecords.querySelectorAll("[data-cancel-fine]")) {
        button.addEventListener(
            "click",
            handleCancelTrafficFine,
        );
    }
}

function renderDeposit() {
    const deposit = summary.caucao;

    if (!deposit) {
        depositRecord.innerHTML = `
            <p class="inspection-records__empty">Nenhuma caução registrada.</p>
        `;
        depositValue.value = "";
        depositReleased.value = "0";
        depositNotes.value = "";
        return;
    }

    depositValue.value = String(
        deposit.valor
    );
    depositReleased.value = String(
        deposit.valor_liberado
    );
    depositNotes.value = (
        deposit.observacoes
        ?? ""
    );

    depositRecord.innerHTML = `
        <article class="inspection-record">
            <div>
                <strong>${formatCurrency(deposit.valor_retido)} retidos</strong>
                <span>${formatCurrency(deposit.valor_liberado)} liberados · ${deposit.status}</span>
            </div>
            <p>${escapeHtml(deposit.observacoes ?? "Sem observações.")}</p>
        </article>
    `;
}

function renderSummary() {
    emptyState.hidden = true;
    content.hidden = false;

    renderRentalSummary();
    renderIndicators();
    renderInspections();
    renderDamages();
    renderTrafficFines();
    renderDeposit();
}

async function loadSummary({
    preserveMessage = false,
} = {}) {
    const rentalId = selectedRentalId();

    if (!rentalId) {
        summary = null;
        content.hidden = true;
        emptyState.hidden = false;
        return;
    }

    if (!preserveMessage) {
        clearMessage(
            pageMessage
        );
    }

    refreshButton.disabled = true;

    try {
        summary = await getInspectionSummary(
            rentalId
        );
        renderSummary();
    } catch (error) {
        if (
            error instanceof ApiError
            && error.status === 401
        ) {
            clearToken();
            goToLogin();
            return;
        }

        showMessage(
            pageMessage,
            error.message,
        );
    } finally {
        refreshButton.disabled = false;
    }
}

async function handleInspectionSubmit(
    event,
) {
    event.preventDefault();

    const rentalId = selectedRentalId();

    if (!rentalId) {
        showMessage(
            pageMessage,
            "Selecione um aluguel.",
        );
        return;
    }

    try {
        await createInspection(
            rentalId,
            {
                tipo: inspectionType.value,
                quilometragem: Number(
                    inspectionOdometer.value
                ),
                combustivel_percentual: Number(
                    inspectionFuel.value
                ),
                observacoes: (
                    inspectionNotes.value.trim()
                    || null
                ),
            },
        );

        inspectionForm.reset();
        await loadSummary({
            preserveMessage: true,
        });
        showMessage(
            pageMessage,
            "Inspeção registrada com sucesso.",
            "success",
        );
    } catch (error) {
        showMessage(
            pageMessage,
            error.message,
        );
    }
}

async function handleDamageSubmit(
    event,
) {
    event.preventDefault();

    const rentalId = selectedRentalId();

    if (!rentalId) {
        showMessage(
            pageMessage,
            "Selecione um aluguel.",
        );
        return;
    }

    try {
        await createDamage(
            rentalId,
            {
                descricao: damageDescription.value.trim(),
                valor_estimado: Number(
                    damageValue.value
                ),
            },
        );

        damageForm.reset();
        damageValue.value = "0";
        await loadSummary({
            preserveMessage: true,
        });
        showMessage(
            pageMessage,
            "Dano registrado com sucesso.",
            "success",
        );
    } catch (error) {
        showMessage(
            pageMessage,
            error.message,
        );
    }
}

async function handleTrafficFineSubmit(
    event,
) {
    event.preventDefault();

    const rentalId = selectedRentalId();

    if (!rentalId) {
        showMessage(
            pageMessage,
            "Selecione um aluguel.",
        );
        return;
    }

    try {
        await createTrafficFine(
            rentalId,
            {
                descricao: trafficFineDescription.value.trim(),
                valor: Number(
                    trafficFineValue.value
                ),
                data_ocorrencia: (
                    trafficFineDate.value
                ),
            },
        );

        trafficFineForm.reset();
        trafficFineValue.value = "0";
        trafficFineDate.value = (
            todayIsoDate()
        );
        await loadSummary({
            preserveMessage: true,
        });
        showMessage(
            pageMessage,
            "Multa de trânsito registrada.",
            "success",
        );
    } catch (error) {
        showMessage(
            pageMessage,
            error.message,
        );
    }
}

async function handleDepositSubmit(
    event,
) {
    event.preventDefault();

    const rentalId = selectedRentalId();

    if (!rentalId) {
        showMessage(
            pageMessage,
            "Selecione um aluguel.",
        );
        return;
    }

    try {
        await saveDeposit(
            rentalId,
            {
                valor: Number(
                    depositValue.value
                ),
                valor_liberado: Number(
                    depositReleased.value
                ),
                observacoes: (
                    depositNotes.value.trim()
                    || null
                ),
            },
        );

        await loadSummary({
            preserveMessage: true,
        });
        showMessage(
            pageMessage,
            "Caução atualizada com sucesso.",
            "success",
        );
    } catch (error) {
        showMessage(
            pageMessage,
            error.message,
        );
    }
}

async function handleCancelDamage(
    event,
) {
    const id = Number(
        event.currentTarget.dataset.cancelDamage
    );

    if (
        !window.confirm(
            "Cancelar este registro de dano?"
        )
    ) {
        return;
    }

    try {
        await cancelDamage(
            id
        );
        await loadSummary({
            preserveMessage: true,
        });
        showMessage(
            pageMessage,
            "Registro de dano cancelado.",
            "success",
        );
    } catch (error) {
        showMessage(
            pageMessage,
            error.message,
        );
    }
}

async function handleCancelTrafficFine(
    event,
) {
    const id = Number(
        event.currentTarget.dataset.cancelFine
    );

    if (
        !window.confirm(
            "Cancelar esta multa de trânsito?"
        )
    ) {
        return;
    }

    try {
        await cancelTrafficFine(
            id
        );
        await loadSummary({
            preserveMessage: true,
        });
        showMessage(
            pageMessage,
            "Multa de trânsito cancelada.",
            "success",
        );
    } catch (error) {
        showMessage(
            pageMessage,
            error.message,
        );
    }
}

async function initialize() {
    if (!(await restoreSession())) {
        goToLogin();
        return;
    }

    try {
        currentUser = await getCurrentUser();
        applyNavigationPermissions(
            currentUser
        );

        roleBadge.textContent = (
            currentUser.role
        );

        if (
            !can(
                Permissions.VISTORIAS_LER
            )
        ) {
            window.location.replace(
                "/app/dashboard.html"
            );
            return;
        }

        rentals = await getRentals();
        populateRentals();

        trafficFineDate.value = (
            todayIsoDate()
        );

        if (selectedRentalId()) {
            await loadSummary();
        }
    } catch (error) {
        if (
            error instanceof ApiError
            && error.status === 401
        ) {
            clearToken();
            goToLogin();
            return;
        }

        showMessage(
            pageMessage,
            error.message
            ?? "Não foi possível preparar a página.",
        );
    }
}

rentalSelect.addEventListener(
    "change",
    () => loadSummary(),
);

refreshButton.addEventListener(
    "click",
    () => loadSummary(),
);

inspectionForm.addEventListener(
    "submit",
    handleInspectionSubmit,
);

damageForm.addEventListener(
    "submit",
    handleDamageSubmit,
);

trafficFineForm.addEventListener(
    "submit",
    handleTrafficFineSubmit,
);

depositForm.addEventListener(
    "submit",
    handleDepositSubmit,
);

logoutButton.addEventListener(
    "click",
    async () => {
        try {
            await logout();
        } finally {
            goToLogin();
        }
    },
);

initialize();
