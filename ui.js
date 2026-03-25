const content = document.getElementById("content");
const refreshBtn = document.getElementById("refreshBtn");

// Manual theming helpers for quick experimentation in ui.js or DevTools.
window.themeTools = {
    setTheme(theme = "dark") {
        // Valid values: "light", "dark", "auto"
        mdui.setTheme(theme);
    },
    setColorScheme(color = "#00ffbf", options) {
        // Example color: "#ff0000"
        mdui.setColorScheme(color, options);
    },
    resetColorScheme() {
        mdui.removeColorScheme();
    },
};

function showToast(message) {
    if (window.mdui && mdui.snackbar) {
        mdui.snackbar({ message });
    }
}

function filterOtherApps(query, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const rows = container.querySelectorAll(".row");
    const searchTerm = query.toLowerCase();

    rows.forEach((row) => {
        const pkg = row.getAttribute("data-pkg") || "";
        const matches = pkg.toLowerCase().includes(searchTerm);
        row.style.display = matches ? "" : "none";
    });
}

function rowActions(pkg, type, hasStore) {
    const uninstallAction = {
        known: "uninstall_known",
        suggested: "uninstall_suggested",
        all_other: "uninstall_other",
    }[type];

    let html = `<mdui-button icon="delete" variant="filled-tonal" onclick="invokeAction('${uninstallAction}', '${pkg}')">Uninstall</mdui-button>`;

    if (type === "all_other") {
        html += `<mdui-button icon="delete" variant="filled" onclick="invokeAction('mark_bad', '${pkg}')">Mark Bad & Uninstall</mdui-button>`;
    }

    if (hasStore) {
        html += `<mdui-button icon="store" variant="outlined" onclick="invokeAction('open_play_store', '${pkg}')">Play Store</mdui-button>`;
    }

    return html;
}

function renderSection(title, items, type) {
    if (!items || items.length === 0) {
        return "";
    }

    const rows = items
        .map(
            (item) => `
      <div class="row">
        <div class="pkg">${item.pkg}</div>
        <div class="actions">${rowActions(item.pkg, type, item.has_store)}</div>
      </div>
    `,
        )
        .join("");

    return `
    <mdui-card class="panel" variant="filled">
      <div class="panel-content">
        <div class="panel-head">
          <div class="panel-title">${title}</div>
          <mdui-chip>${items.length}</mdui-chip>
        </div>
        ${rows}
      </div>
    </mdui-card>
  `;
}

function renderOtherSection(items) {
    if (!items || items.length === 0) {
        return "";
    }

    const searchInputId = "otherAppsSearch";
    const itemsContainerId = "otherAppsItems";

    const rows = items
        .map(
            (item) => `
      <div class="row" data-pkg="${item.pkg}">
        <div class="pkg">${item.pkg}</div>
        <div class="actions">${rowActions(item.pkg, "all_other", item.has_store)}</div>
      </div>
    `,
        )
        .join("");

    return `
    <mdui-card class="panel" variant="filled">
      <div class="other-content">
        <mdui-collapse>
          <mdui-collapse-item>
            <div slot="header" class="other-header">
              <div class="other-header-side other-header-left">
                <mdui-button variant="text">All Other Apps</mdui-button>
              </div>
              <div class="other-header-center">
                <mdui-text-field
                  id="${searchInputId}"
                  variant="outlined"
                  label="Search"
                  type="search"
                  clearable
                  icon="search"
                  placeholder="Package name"
                  class="other-search"
                  onkeyup="filterOtherApps(this.value, '${itemsContainerId}')"
                ></mdui-text-field>
              </div>
              <div class="other-header-side other-header-right">
                <mdui-chip>${items.length}</mdui-chip>
              </div>
            </div>
            <div class="other-inner" id="${itemsContainerId}">${rows}</div>
          </mdui-collapse-item>
        </mdui-collapse>
      </div>
    </mdui-card>
  `;
}

window.renderState = function renderState(state) {
    const known = renderSection("Known Bad Apps", state.known_bad, "known");
    const suggested = renderSection(
        "Suggested Suspicious Apps",
        state.suggested,
        "suggested",
    );
    const allOther = renderOtherSection(state.all_other);

    let empty = "";
    if (state.empty) {
        empty = `
      <mdui-card class="no-data" variant="filled">
        <div class="empty-message">No apps detected. For deeper cleaning, contact Caleb.</div>
      </mdui-card>
    `;
    } else if (!state.has_alerts) {
        empty = `
      <mdui-card class="no-data" variant="filled">
        <div class="empty-message">No dodgy apps detected. For deeper cleaning, contact Caleb.</div>
      </mdui-card>
    `;
    }

    content.innerHTML = `${known}${suggested}${allOther}${empty}`;
};

window.invokeAction = async function invokeAction(action, pkg) {
    try {
        const fn = window.pywebview?.api?.[action];
        if (!fn) {
            return;
        }

        const next = await fn(pkg);
        if (next && typeof next === "object") {
            window.renderState(next);
        }

        if (action !== "open_play_store") {
            showToast("Updated");
        }
    } catch (error) {
        showToast("Action failed");
        console.error(error);
    }
};

async function initialLoad() {
    try {
        // Initialize theme and color scheme on page load
        window.themeTools.setTheme("dark");
        window.themeTools.setColorScheme("#00ffbf");

        const state = await window.pywebview.api.get_state();
        window.renderState(state);
    } catch (error) {
        content.innerHTML =
            '<mdui-card variant="filled"><div class="load-error">Unable to load app data.</div></mdui-card>';
        console.error(error);
    }
}

refreshBtn.addEventListener("click", async () => {
    try {
        const state = await window.pywebview.api.refresh();
        window.renderState(state);
        showToast("Refreshed");
    } catch (error) {
        showToast("Refresh failed");
        console.error(error);
    }
});

window.addEventListener("pywebviewready", initialLoad);
