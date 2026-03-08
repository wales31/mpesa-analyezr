const dashboardState = {
  range: { from: null, to: null, label: "Last 30 days", preset: "last_30" },
  summary: null,
  insights: null,
  transactions: null,
  notifications: null,
  budgetLimit: null,
};

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function getTxLimit() {
  const raw = byId("txLimit")?.value ?? "25";
  const parsed = Number(raw);
  const n = Number.isFinite(parsed) ? Math.trunc(parsed) : 25;
  return Math.min(200, Math.max(1, n));
}

function hasAuthToken() {
  return Boolean(window.mpesaApi?.getToken?.());
}

function ensureAuthenticated() {
  if (hasAuthToken()) return;
  throw new Error("Sign in to load live insights.");
}

function toInputDate(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

function parseInputDate(value) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(String(value || ""))) return null;
  const dt = new Date(`${value}T00:00:00`);
  return Number.isNaN(dt.getTime()) ? null : dt;
}

function startOfDayIso(date) {
  const copy = new Date(date);
  copy.setHours(0, 0, 0, 0);
  return copy.toISOString();
}

function endOfDayIso(date) {
  const copy = new Date(date);
  copy.setHours(23, 59, 59, 999);
  return copy.toISOString();
}

function buildQueryString(range, extra = {}) {
  const params = new URLSearchParams();
  if (range?.from) params.set("from", range.from);
  if (range?.to) params.set("to", range.to);

  Object.entries(extra).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") return;
    params.set(key, String(value));
  });

  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

function resolveSelectedRange() {
  const preset = byId("rangePreset")?.value || "last_30";
  const now = new Date();

  if (preset === "all") {
    return {
      preset,
      label: "All time",
      from: null,
      to: null,
      fromInput: "",
      toInput: "",
    };
  }

  if (preset === "this_month") {
    const start = new Date(now.getFullYear(), now.getMonth(), 1);
    return {
      preset,
      label: "This month",
      from: startOfDayIso(start),
      to: endOfDayIso(now),
      fromInput: toInputDate(start),
      toInput: toInputDate(now),
    };
  }

  if (preset === "last_7" || preset === "last_30") {
    const days = preset === "last_7" ? 7 : 30;
    const start = new Date(now);
    start.setDate(start.getDate() - (days - 1));

    return {
      preset,
      label: `Last ${days} days`,
      from: startOfDayIso(start),
      to: endOfDayIso(now),
      fromInput: toInputDate(start),
      toInput: toInputDate(now),
    };
  }

  const fromValue = byId("rangeFrom")?.value || "";
  const toValue = byId("rangeTo")?.value || "";
  const fromDate = parseInputDate(fromValue);
  const toDate = parseInputDate(toValue);

  if (!fromDate || !toDate) {
    throw new Error("Choose both From and To dates for a custom range.");
  }
  if (toDate.getTime() < fromDate.getTime()) {
    throw new Error("Custom range is invalid: To date must be after From date.");
  }

  return {
    preset,
    label: `${fromValue} to ${toValue}`,
    from: startOfDayIso(fromDate),
    to: endOfDayIso(toDate),
    fromInput: fromValue,
    toInput: toValue,
  };
}

function applyRangeUiState() {
  const preset = byId("rangePreset")?.value || "last_30";
  const isCustom = preset === "custom";

  const fromEl = byId("rangeFrom");
  const toEl = byId("rangeTo");

  if (fromEl) fromEl.disabled = !isCustom;
  if (toEl) toEl.disabled = !isCustom;

  if (!isCustom) {
    const resolved = resolveSelectedRange();
    if (fromEl) fromEl.value = resolved.fromInput;
    if (toEl) toEl.value = resolved.toInput;
    setText("rangeLabel", resolved.label);
    return;
  }

  if (!fromEl?.value || !toEl?.value) {
    const now = new Date();
    const start = new Date(now);
    start.setDate(start.getDate() - 29);
    if (fromEl && !fromEl.value) fromEl.value = toInputDate(start);
    if (toEl && !toEl.value) toEl.value = toInputDate(now);
  }
  setText("rangeLabel", "Custom range");
}

function buildSignalCard({ title, value, detail, tone = "neutral" }) {
  const toneClass =
    tone === "warning"
      ? "app-signal-warning"
      : tone === "good"
        ? "app-signal-good"
        : "app-signal-neutral";

  return `
    <article class="app-signal-card ${toneClass}">
      <div class="small text-secondary">${escapeHtml(title)}</div>
      <div class="fw-semibold">${escapeHtml(value)}</div>
      <div class="small text-secondary">${escapeHtml(detail)}</div>
    </article>
  `;
}

function deriveExpenseTransactions() {
  const txs = Array.isArray(dashboardState.transactions?.transactions)
    ? dashboardState.transactions.transactions
    : [];
  return txs.filter(
    (tx) =>
      tx?.direction === "expense" &&
      typeof tx?.amount === "number" &&
      Number.isFinite(tx.amount) &&
      tx.amount > 0,
  );
}

function updateKpis() {
  const summary = dashboardState.summary;
  const currency = summary?.currency || "KES";
  const txs = Array.isArray(dashboardState.transactions?.transactions)
    ? dashboardState.transactions.transactions
    : [];
  const expenses = deriveExpenseTransactions();

  const count = txs.length;
  setText("kpiCount", String(count));

  if (!expenses.length) {
    setText("kpiAvgTx", "—");
    setText("kpiActiveDays", "—");
    setText("kpiLargestTx", "—");
    return;
  }

  const expenseTotal = expenses.reduce((sum, tx) => sum + tx.amount, 0);
  const avg = expenseTotal / expenses.length;
  setText("kpiAvgTx", formatCurrency(avg, currency));

  const dayKeys = new Set(
    expenses
      .map((tx) => (tx?.occurred_at ? String(tx.occurred_at).slice(0, 10) : ""))
      .filter(Boolean),
  );
  setText("kpiActiveDays", String(dayKeys.size));

  const largest = expenses.reduce((best, tx) => (tx.amount > best.amount ? tx : best), expenses[0]);
  setText("kpiLargestTx", formatCurrency(largest.amount, currency));
}

function renderSignalCards() {
  const box = byId("insightCards");
  if (!box) return;

  const summary = dashboardState.summary;
  const insights = dashboardState.insights;
  const budgetLimit = dashboardState.budgetLimit;
  const currency = summary?.currency || "KES";

  if (!summary && !insights) {
    box.innerHTML = `<div class="text-secondary small">Load insights to see signal cards.</div>`;
    return;
  }

  const cards = [];

  const totalSpent = typeof summary?.total_spent === "number" ? summary.total_spent : 0;
  const categories = Array.isArray(summary?.categories) ? summary.categories : [];

  if (totalSpent > 0) {
    const top = categories[0];
    const topShare = top && top.amount > 0 ? (top.amount / totalSpent) * 100 : 0;
    const concentrationTone = topShare >= 55 ? "warning" : "good";

    cards.push(
      buildSignalCard({
        title: "Spend concentration",
        value: `${topShare.toFixed(0)}%`,
        detail: top ? `${top.category} holds the largest share` : "No dominant category yet",
        tone: concentrationTone,
      }),
    );

    const rangeDays = (() => {
      const from = dashboardState.range?.from ? new Date(dashboardState.range.from) : null;
      const to = dashboardState.range?.to ? new Date(dashboardState.range.to) : null;
      if (!from || !to || Number.isNaN(from.getTime()) || Number.isNaN(to.getTime())) return null;
      const ms = Math.max(1, to.getTime() - from.getTime());
      return Math.max(1, Math.round(ms / (1000 * 60 * 60 * 24)));
    })();

    if (rangeDays) {
      const daily = totalSpent / rangeDays;
      cards.push(
        buildSignalCard({
          title: "Spend pace",
          value: formatCurrency(daily, currency),
          detail: `Per day over ${rangeDays} days`,
          tone: "neutral",
        }),
      );
    }
  }

  if (budgetLimit?.monthly_budget > 0) {
    const usage = totalSpent / budgetLimit.monthly_budget;
    const percent = Math.round(usage * 100);
    cards.push(
      buildSignalCard({
        title: "Budget usage",
        value: `${percent}%`,
        detail: `${formatCurrency(totalSpent, budgetLimit.currency)} of ${formatCurrency(
          budgetLimit.monthly_budget,
          budgetLimit.currency,
        )}`,
        tone: usage >= 1 ? "warning" : usage >= 0.8 ? "neutral" : "good",
      }),
    );
  } else {
    cards.push(
      buildSignalCard({
        title: "Budget usage",
        value: "Not set",
        detail: "Set a monthly limit on the Budget page to track pressure.",
        tone: "neutral",
      }),
    );
  }

  const warnings = Array.isArray(insights?.warnings) ? insights.warnings.length : 0;
  const highlights = Array.isArray(insights?.highlights) ? insights.highlights.length : 0;
  cards.push(
    buildSignalCard({
      title: "Insight mix",
      value: `${warnings} warnings / ${highlights} highlights`,
      detail: "Based on your current transaction history.",
      tone: warnings > 0 ? "warning" : "good",
    }),
  );

  box.innerHTML = cards.join("");
}

function renderSummary(summary) {
  dashboardState.summary = summary;

  const currency = summary?.currency || "KES";
  const totalSpent = typeof summary?.total_spent === "number" ? summary.total_spent : null;
  const categories = Array.isArray(summary?.categories) ? summary.categories : [];

  setText("kpiTotal", totalSpent === null ? "—" : formatCurrency(totalSpent, currency));

  if (categories.length) {
    const top = categories.reduce((best, cur) => ((cur?.amount ?? 0) > (best?.amount ?? 0) ? cur : best));
    setText("kpiTopCat", top?.category ? String(top.category) : "—");
  } else {
    setText("kpiTopCat", "—");
  }

  const chart = byId("catChart");
  if (!chart) return;

  if (!categories.length) {
    chart.innerHTML = `<div class="text-secondary small">No category data yet.</div>`;
    updateKpis();
    renderSignalCards();
    return;
  }

  const maxAmount = Math.max(...categories.map((c) => (typeof c?.amount === "number" ? c.amount : 0)), 1);

  chart.innerHTML = "";
  for (const c of categories) {
    const name = c?.category ? String(c.category) : "unknown";
    const amount = typeof c?.amount === "number" ? c.amount : 0;
    const pct = Math.min(100, Math.max(0, Math.round((amount / maxAmount) * 100)));

    const row = document.createElement("div");
    row.className = "vstack gap-1";
    row.innerHTML = `
      <div class="d-flex align-items-center justify-content-between gap-2">
        <div class="small text-truncate" title="${escapeHtml(name)}">${escapeHtml(name)}</div>
        <div class="small text-secondary">${formatCurrency(amount, currency)}</div>
      </div>
      <div class="progress" role="progressbar" aria-label="${escapeHtml(name)}" aria-valuenow="${pct}" aria-valuemin="0" aria-valuemax="100" style="height: .5rem;">
        <div class="progress-bar" style="width: ${pct}%"></div>
      </div>
    `;
    chart.appendChild(row);
  }

  updateKpis();
  renderSignalCards();
}

function renderInsights(insights) {
  dashboardState.insights = insights;

  const box = byId("insightsBox");
  if (!box) return;

  const warnings = Array.isArray(insights?.warnings) ? insights.warnings : [];
  const highlights = Array.isArray(insights?.highlights) ? insights.highlights : [];

  if (!warnings.length && !highlights.length) {
    box.innerHTML = `<div class="text-secondary small">No insights yet.</div>`;
    renderSignalCards();
    return;
  }

  box.innerHTML = "";
  for (const w of warnings) {
    const div = document.createElement("div");
    div.className = "alert alert-warning py-2 mb-0";
    div.textContent = String(w);
    box.appendChild(div);
  }
  for (const h of highlights) {
    const div = document.createElement("div");
    div.className = "alert alert-info py-2 mb-0";
    div.textContent = String(h);
    box.appendChild(div);
  }

  renderSignalCards();
}

function renderTransactions(payload) {
  dashboardState.transactions = payload;

  const tbody = byId("txBody");
  if (!tbody) return;

  const transactions = Array.isArray(payload?.transactions) ? payload.transactions : [];
  const count = typeof payload?.count === "number" ? payload.count : transactions.length;

  setText("kpiCount", String(count));

  if (!transactions.length) {
    tbody.innerHTML = `
      <tr>
        <td colspan="6" class="text-secondary">No transactions found in this range.</td>
      </tr>
    `;
    updateKpis();
    renderSignalCards();
    return;
  }

  tbody.innerHTML = "";
  for (const tx of transactions) {
    const tr = document.createElement("tr");
    const currency = tx?.currency || "KES";
    tr.innerHTML = `
      <td class="text-secondary">${tx?.id ?? "—"}</td>
      <td>${formatCurrency(typeof tx?.amount === "number" ? tx.amount : NaN, currency)}</td>
      <td>${escapeHtml(tx?.category ?? "—")}</td>
      <td class="text-secondary">${escapeHtml(tx?.transaction_type ?? "—")}</td>
      <td>${escapeHtml(tx?.recipient ?? "—")}</td>
      <td class="text-secondary">${formatDateTime(tx?.occurred_at)}</td>
    `;
    tbody.appendChild(tr);
  }

  updateKpis();
  renderSignalCards();
}

function renderNotifications(payload) {
  dashboardState.notifications = payload;

  const box = byId("notifBox");
  const badge = byId("notifUnreadBadge");
  if (!box || !badge) return;

  const notifications = Array.isArray(payload?.notifications) ? payload.notifications : [];
  const unread = typeof payload?.unread === "number" ? payload.unread : 0;
  badge.textContent = String(unread);
  badge.className = `badge ms-1 ${unread > 0 ? "text-bg-warning" : "text-bg-secondary"}`;

  if (!notifications.length) {
    box.innerHTML = `<div class="text-secondary small">No notifications yet.</div>`;
    return;
  }

  box.innerHTML = "";
  for (const n of notifications) {
    const severity = String(n?.severity || "info");
    const title = String(n?.title || "Notification");
    const message = String(n?.message || "");
    const read = Boolean(n?.is_read);
    const cls = severity === "warning" ? "alert-warning" : "alert-info";

    const row = document.createElement("div");
    row.className = `alert ${cls} py-2 mb-0 ${read ? "opacity-75" : ""}`;
    row.innerHTML = `
      <div class="d-flex align-items-start justify-content-between gap-2">
        <div>
          <div class="fw-semibold small">${escapeHtml(title)}</div>
          <div class="small">${escapeHtml(message)}</div>
        </div>
        <div class="text-nowrap text-secondary small">${read ? "Read" : "Unread"}</div>
      </div>
    `;
    box.appendChild(row);
  }
}

async function loadSummary() {
  ensureAuthenticated();
  setHtml("catChart", `<div class="text-secondary small">Loading…</div>`);
  const data = await window.mpesaApi.get(`/summary${buildQueryString(dashboardState.range)}`);
  renderSummary(data);
  return data;
}

async function loadInsights() {
  ensureAuthenticated();
  setHtml("insightsBox", `<div class="text-secondary small">Loading…</div>`);
  const data = await window.mpesaApi.get("/insights");
  renderInsights(data);
  return data;
}

async function loadTransactions() {
  ensureAuthenticated();
  const limit = getTxLimit();
  setHtml("txBody", `<tr><td colspan="6" class="text-secondary">Loading…</td></tr>`);
  const data = await window.mpesaApi.get(
    `/transactions${buildQueryString(dashboardState.range, { limit })}`,
  );
  renderTransactions(data);
  return data;
}

async function loadNotifications({ refresh = false } = {}) {
  ensureAuthenticated();
  setHtml("notifBox", `<div class="text-secondary small">Loading…</div>`);
  if (refresh) await window.mpesaApi.post("/notifications/refresh", {});
  const data = await window.mpesaApi.get("/notifications?limit=20");
  renderNotifications(data);
  return data;
}

async function loadBudgetLimit() {
  if (!hasAuthToken()) {
    dashboardState.budgetLimit = null;
    renderSignalCards();
    return null;
  }

  try {
    const data = await window.mpesaApi.get("/budget/limit");
    dashboardState.budgetLimit = data;
    renderSignalCards();
    return data;
  } catch (error) {
    dashboardState.budgetLimit = null;
    renderSignalCards();

    const message = String(error?.message || "").toLowerCase();
    if (message.includes("not set")) return null;
    return null;
  }
}

async function markAllNotificationsRead() {
  ensureAuthenticated();
  await window.mpesaApi.post("/notifications/read-all", {});
  return loadNotifications();
}

function renderOfflineState(message = "API offline. Start the backend and try again.") {
  setText("kpiTotal", "—");
  setText("kpiTopCat", "—");
  setText("kpiCount", "—");
  setText("kpiAvgTx", "—");
  setText("kpiActiveDays", "—");
  setText("kpiLargestTx", "—");
  setText("notifUnreadBadge", "0");
  setHtml("catChart", `<div class="text-danger small">${escapeHtml(message)}</div>`);
  setHtml("insightsBox", `<div class="text-danger small">${escapeHtml(message)}</div>`);
  setHtml("insightCards", `<div class="text-danger small">${escapeHtml(message)}</div>`);
  setHtml("notifBox", `<div class="text-danger small">${escapeHtml(message)}</div>`);
  setHtml("txBody", `<tr><td colspan="6" class="text-danger">${escapeHtml(message)}</td></tr>`);
}

function renderAuthRequiredState() {
  const message = "Sign in to load live insights and transactions.";
  setText("kpiTotal", "—");
  setText("kpiTopCat", "—");
  setText("kpiCount", "—");
  setText("kpiAvgTx", "—");
  setText("kpiActiveDays", "—");
  setText("kpiLargestTx", "—");
  setText("notifUnreadBadge", "0");

  setHtml(
    "catChart",
    `<div class="text-secondary small">${message} <a href="./auth.html">Open sign in</a>.</div>`,
  );
  setHtml(
    "insightsBox",
    `<div class="text-secondary small">${message} <a href="./auth.html">Open sign in</a>.</div>`,
  );
  setHtml(
    "insightCards",
    `<div class="text-secondary small">${message} <a href="./auth.html">Open sign in</a>.</div>`,
  );
  setHtml(
    "notifBox",
    `<div class="text-secondary small">${message} <a href="./auth.html">Open sign in</a>.</div>`,
  );
  setHtml(
    "txBody",
    `<tr><td colspan="6" class="text-secondary">${message} <a href="./auth.html">Open sign in</a>.</td></tr>`,
  );
}

function applyRangeOrShowError() {
  try {
    dashboardState.range = resolveSelectedRange();
    setText("rangeLabel", dashboardState.range.label);
    return true;
  } catch (error) {
    setText("rangeLabel", "Range error");
    const dev = byId("devOutput");
    if (dev) dev.textContent = `Range error: ${error.message}`;
    return false;
  }
}

async function refreshAll({ skipHealthCheck = false } = {}) {
  const dev = byId("devOutput");
  if (dev) dev.textContent = "";

  if (!applyRangeOrShowError()) return null;

  if (!hasAuthToken()) {
    renderAuthRequiredState();
    return null;
  }

  if (!skipHealthCheck) {
    const health = await window.mpesaApi.check();
    if (!health) {
      renderOfflineState();
      return null;
    }
  }

  const tasks = [
    loadSummary().catch((e) => {
      setHtml("catChart", `<div class="text-danger small">Error: ${escapeHtml(String(e.message))}</div>`);
      return null;
    }),
    loadInsights().catch((e) => {
      setHtml("insightsBox", `<div class="text-danger small">Error: ${escapeHtml(String(e.message))}</div>`);
      return null;
    }),
    loadTransactions().catch((e) => {
      setHtml("txBody", `<tr><td colspan="6" class="text-danger">Error: ${escapeHtml(String(e.message))}</td></tr>`);
      return null;
    }),
    loadNotifications({ refresh: true }).catch((e) => {
      setHtml("notifBox", `<div class="text-danger small">Error: ${escapeHtml(String(e.message))}</div>`);
      return null;
    }),
    loadBudgetLimit().catch(() => null),
  ];

  await Promise.allSettled(tasks);
  renderSignalCards();
  updateKpis();
  return true;
}

function resetDashboard() {
  dashboardState.summary = null;
  dashboardState.insights = null;
  dashboardState.transactions = null;
  dashboardState.notifications = null;
  dashboardState.budgetLimit = null;

  setText("kpiTotal", "—");
  setText("kpiTopCat", "—");
  setText("kpiCount", "—");
  setText("kpiAvgTx", "—");
  setText("kpiActiveDays", "—");
  setText("kpiLargestTx", "—");
  setText("notifUnreadBadge", "0");

  setHtml("catChart", `<div class="text-secondary small">Load summary to see category totals.</div>`);
  setHtml("insightsBox", `<div class="text-secondary small">Load insights to see warnings and highlights.</div>`);
  setHtml("insightCards", `<div class="text-secondary small">Load insights to see signal cards.</div>`);
  setHtml("notifBox", `<div class="text-secondary small">Load notifications to see budget alerts and spending insights.</div>`);
  setHtml("txBody", `<tr><td colspan="6" class="text-secondary">No data loaded yet.</td></tr>`);

  const rangePreset = byId("rangePreset");
  if (rangePreset) rangePreset.value = "last_30";
  applyRangeUiState();
  applyRangeOrShowError();
}

document.addEventListener("DOMContentLoaded", () => {
  byId("rangePreset")?.addEventListener("change", () => {
    applyRangeUiState();
  });

  byId("btnApplyRange")?.addEventListener("click", async () => {
    await refreshAll();
  });

  byId("btnLoadSummary")?.addEventListener("click", async () => {
    try {
      if (!applyRangeOrShowError()) return;
      await loadSummary();
    } catch (e) {
      setHtml("catChart", `<div class="text-danger small">Error: ${escapeHtml(String(e.message))}</div>`);
    }
  });

  byId("btnLoadInsights")?.addEventListener("click", async () => {
    try {
      await loadInsights();
    } catch (e) {
      setHtml("insightsBox", `<div class="text-danger small">Error: ${escapeHtml(String(e.message))}</div>`);
    }
  });

  byId("btnLoadTransactions")?.addEventListener("click", async () => {
    try {
      if (!applyRangeOrShowError()) return;
      await loadTransactions();
    } catch (e) {
      setHtml("txBody", `<tr><td colspan="6" class="text-danger">Error: ${escapeHtml(String(e.message))}</td></tr>`);
    }
  });

  byId("btnRefreshNotifs")?.addEventListener("click", async () => {
    try {
      await loadNotifications({ refresh: true });
    } catch (e) {
      setHtml("notifBox", `<div class="text-danger small">Error: ${escapeHtml(String(e.message))}</div>`);
    }
  });

  byId("btnMarkNotifsRead")?.addEventListener("click", async () => {
    try {
      await markAllNotificationsRead();
    } catch (e) {
      setHtml("notifBox", `<div class="text-danger small">Error: ${escapeHtml(String(e.message))}</div>`);
    }
  });

  byId("btnApplyTx")?.addEventListener("click", async () => {
    try {
      if (!applyRangeOrShowError()) return;
      await loadTransactions();
    } catch (e) {
      setHtml("txBody", `<tr><td colspan="6" class="text-danger">Error: ${escapeHtml(String(e.message))}</td></tr>`);
    }
  });

  byId("btnRefreshAll")?.addEventListener("click", async () => {
    await refreshAll();
  });

  byId("btnDeleteAll")?.addEventListener("click", async () => {
    const dev = byId("devOutput");
    if (dev) dev.textContent = "";
    try {
      ensureAuthenticated();
      const data = await window.mpesaApi.del("/transactions");
      if (dev) dev.textContent = pretty(data);
      resetDashboard();
    } catch (e) {
      if (dev) dev.textContent = `Error: ${e.message}`;
    }
  });

  resetDashboard();

  (async () => {
    if (!hasAuthToken()) {
      renderAuthRequiredState();
      return;
    }

    const health = await (window.mpesaApp?.apiCheckPromise ?? window.mpesaApi.check());
    if (!health) {
      renderOfflineState();
      return;
    }
    await refreshAll({ skipHealthCheck: true });
  })();
});
