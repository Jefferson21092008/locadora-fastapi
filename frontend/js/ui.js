const NETWORK_STATUS_ID = "network-status";

function isEditableTarget(target) {
    return target instanceof HTMLElement && (
        target.matches("input:not([type='search']), textarea, select")
        || target.isContentEditable
    );
}

function visibleSearchInputs() {
    return [...document.querySelectorAll("input[type='search']")]
        .filter((input) => !input.disabled && input.offsetParent !== null);
}

function setupLiveRegions() {
    for (const element of document.querySelectorAll("[role='status'], [aria-live]")) {
        element.setAttribute("aria-atomic", "true");
    }
}

function setupSearchShortcuts() {
    const searchInputs = document.querySelectorAll("input[type='search']");

    for (const input of searchInputs) {
        input.setAttribute("aria-keyshortcuts", "/");

        input.addEventListener("keydown", (event) => {
            if (event.key !== "Escape" || !input.value) {
                return;
            }

            event.preventDefault();
            input.value = "";
            input.dispatchEvent(new Event("input", { bubbles: true }));
        });
    }

    document.addEventListener("keydown", (event) => {
        if (
            event.key !== "/"
            || event.ctrlKey
            || event.metaKey
            || event.altKey
            || isEditableTarget(event.target)
        ) {
            return;
        }

        const [searchInput] = visibleSearchInputs();
        if (!searchInput) {
            return;
        }

        event.preventDefault();
        searchInput.focus();
    });
}

function setupDialogFocus() {
    const dialogs = [...document.querySelectorAll("dialog")];
    const returnFocus = new WeakMap();
    const previouslyOpen = new WeakSet();

    for (const dialog of dialogs) {
        if (dialog.open) {
            previouslyOpen.add(dialog);
        }

        dialog.addEventListener("close", () => {
            previouslyOpen.delete(dialog);
            const trigger = returnFocus.get(dialog);

            if (
                trigger instanceof HTMLElement
                && trigger.isConnected
                && !trigger.hidden
                && !trigger.matches(":disabled")
            ) {
                trigger.focus();
            }

            returnFocus.delete(dialog);
        });
    }

    document.addEventListener("click", (event) => {
        const trigger = event.target instanceof Element
            ? event.target.closest("button, a")
            : null;

        if (!(trigger instanceof HTMLElement)) {
            return;
        }

        queueMicrotask(() => {
            for (const dialog of dialogs) {
                if (dialog.open && !previouslyOpen.has(dialog)) {
                    previouslyOpen.add(dialog);
                    returnFocus.set(dialog, trigger);
                }
            }
        });
    });
}

function syncFormBusyState(form) {
    const submitButton = form.querySelector("button[type='submit'], input[type='submit']");
    if (!submitButton) {
        return;
    }

    const update = () => {
        if (submitButton.disabled) {
            form.setAttribute("aria-busy", "true");
        } else {
            form.removeAttribute("aria-busy");
        }
    };

    update();
    new MutationObserver(update).observe(submitButton, {
        attributes: true,
        attributeFilter: ["disabled"],
    });
}

function setupFormBusyStates() {
    for (const form of document.querySelectorAll("form")) {
        syncFormBusyState(form);
    }
}

function setupNetworkStatus() {
    const region = document.createElement("div");
    region.id = NETWORK_STATUS_ID;
    region.className = "network-status";
    region.setAttribute("role", "status");
    region.setAttribute("aria-live", "polite");
    region.setAttribute("aria-atomic", "true");
    region.hidden = true;
    document.body.append(region);

    let wasOffline = !navigator.onLine;
    let hideTimer = null;

    const render = () => {
        if (hideTimer) {
            window.clearTimeout(hideTimer);
            hideTimer = null;
        }

        if (!navigator.onLine) {
            wasOffline = true;
            region.textContent = "Sem conexão. Algumas ações podem ficar indisponíveis.";
            region.className = "network-status network-status--offline";
            region.hidden = false;
            return;
        }

        if (!wasOffline) {
            region.hidden = true;
            return;
        }

        wasOffline = false;
        region.textContent = "Conexão restaurada.";
        region.className = "network-status network-status--online";
        region.hidden = false;
        hideTimer = window.setTimeout(() => {
            region.hidden = true;
        }, 3000);
    };

    window.addEventListener("offline", render);
    window.addEventListener("online", render);
    render();
}

function init() {
    setupLiveRegions();
    setupSearchShortcuts();
    setupDialogFocus();
    setupFormBusyStates();
    setupNetworkStatus();
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
} else {
    init();
}
