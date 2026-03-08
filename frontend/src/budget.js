function byId(id) {
  return document.getElementById(id);
}

function nowMonth() {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  return `${y}-${m}`;
}

function budgetKey(month) {
  return `mpesa_budget_v1_${month}`;
}

function parseMoney(value) {
  const n = Number(value);
  return Number.isFinite(n) ? n : 0;
}

function formatMoney(value) {
  if (typeof value !== "number" || !Number.isFinite(value)) return "—";
  return `KES ${new Intl.NumberFormat(undefined, { maximumFractionDigits: 2 }).format(value)}`;
}

function defaultBudgetRows() {
  return [
    { category: "food", planned: 0 },
    { category: "transport", planned: 0 },
    { category: "rent", planned: 0 },
    { category: "airtime", planned: 0 },
    { category: "bills", planned: 0 },
  ];
}

function loadBudget(month) {
  try {
    const raw = localStorage.getItem(budgetKey(month));
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object") return null;
    return parsed;
  } catch {
    return null;
  }
}

function saveBudget(month, data) {
  localStorage.setItem(budgetKey(month), JSON.stringify(data));
}

function collectBudget() {
  const month = byId("budgetMonth")?.value || nowMonth();
  const income = parseMoney(byId("budgetIncome")?.value);

  const rows = [];
  const tbody = byId("budgetBody");
  const trList = tbody ? Array.from(tbody.querySelectorAll("tr")) : [];
  for (const tr of trList) {
    const category = tr.querySelector('[data-role="category"]')?.value?.trim() ?? "";
    const planned = parseMoney(tr.querySelector('[data-role="planned"]')?.value);
    if (!category && planned === 0) continue;
    rows.push({ category, planned });
  }

  return { month, income, rows };
}

function computePlannedTotal(rows) {
  return rows.reduce((sum, r) => sum + (typeof r.planned === "number" ? r.planned : 0), 0);
}

function setStatus({ income, plannedTotal }) {
  const unallocated = income - plannedTotal;
  const status = byId("budgetStatus");
  if (!status) return;

  if (income <= 0 && plannedTotal <= 0) {
    status.textContent = "";
    return;
  }

  if (unallocated < 0) {
    status.textContent = "Over-allocated";
    status.className = "text-danger small";
    return;
  }

  if (unallocated === 0 && income > 0) {
    status.textContent = "Zero-based";
    status.className = "text-success small";
    return;
  }

  status.textContent = "In progress";
  status.className = "text-secondary small";
}

function updateBudgetKpis({ income, plannedTotal }) {
  const unallocated = income - plannedTotal;
  const unallocatedEl = byId("kpiBudgetUnallocated");
  if (unallocatedEl) {
    unallocatedEl.textContent = formatMoney(unallocated);
    unallocatedEl.classList.toggle("text-danger", unallocated < 0);
    unallocatedEl.classList.toggle("text-success", unallocated === 0 && income > 0);
  }

  const incomeEl = byId("kpiBudgetIncome");
  if (incomeEl) incomeEl.textContent = formatMoney(income);

  const plannedEl = byId("kpiBudgetPlanned");
  if (plannedEl) plannedEl.textContent = formatMoney(plannedTotal);

  setStatus({ income, plannedTotal });
}

function createBudgetRow({ category = "", planned = 0 } = {}) {
  const tr = document.createElement("tr");
  tr.innerHTML = `
    <td>
      <input
        class="form-control form-control-sm"
        type="text"
        data-role="category"
        placeholder="e.g., food"
        value="${escapeHtml(category)}"
      />
    </td>
    <td>
      <input
        class="form-control form-control-sm"
        type="number"
        min="0"
        step="0.01"
        data-role="planned"
        value="${Number.isFinite(planned) ? planned : 0}"
      />
    </td>
    <td class="text-end">
      <button class="btn btn-outline-secondary btn-sm" type="button" data-role="remove" aria-label="Remove row">
        ✕
      </button>
    </td>
  `;

  tr.querySelector('[data-role="remove"]')?.addEventListener("click", () => {
    tr.remove();
    recalc();
  });

  tr.querySelector('[data-role="category"]')?.addEventListener("input", () => recalc());
  tr.querySelector('[data-role="planned"]')?.addEventListener("input", () => recalc());

  return tr;
}

function escapeHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderBudgetRows(rows) {
  const tbody = byId("budgetBody");
  if (!tbody) return;
  tbody.innerHTML = "";
  for (const row of rows) tbody.appendChild(createBudgetRow(row));
}

function recalc() {
  const { income, rows } = collectBudget();
  const plannedTotal = computePlannedTotal(rows);
  updateBudgetKpis({ income, plannedTotal });
}

function renderActuals({ plannedRows, summary }) {
  const container = byId("budgetActuals");
  if (!container) return;

  const categories = Array.isArray(summary?.categories) ? summary.categories : [];
  const currency = summary?.currency || "KES";

  if (!categories.length) {
    container.innerHTML = `<div class="text-secondary small">No category totals returned yet.</div>`;
    return;
  }

  const plannedByCategory = new Map();
  for (const r of plannedRows) {
    const key = (r?.category ?? "").trim().toLowerCase();
    if (!key) continue;
    plannedByCategory.set(key, parseMoney(r.planned));
  }

  const maxActual = Math.max(
    1,
    ...categories.map((c) => (typeof c?.amount === "number" ? c.amount : 0)),
  );

  container.innerHTML = "";

  const total = typeof summary?.total_spent === "number" ? summary.total_spent : null;
  if (total !== null) {
    const top = document.createElement("div");
    top.className = "app-kpi p-3";
    top.innerHTML = `
      <div class="text-secondary small">Total actual spending</div>
      <div class="fs-6 fw-semibold">${formatMoney(total).replace("KES", currency)}</div>
    `;
    container.appendChild(top);
  }

  for (const c of categories) {
    const rawName = c?.category ? String(c.category) : "unknown";
    const key = rawName.trim().toLowerCase();
    const actual = typeof c?.amount === "number" ? c.amount : 0;
    const planned = plannedByCategory.has(key) ? plannedByCategory.get(key) : null;

    const pct = Math.min(100, Math.max(0, Math.round((actual / maxActual) * 100)));
    const over = planned !== null && actual > planned && planned > 0;

    const card = document.createElement("div");
    card.className = "vstack gap-1";
    card.innerHTML = `
      <div class="d-flex align-items-center justify-content-between gap-2">
        <div class="small text-truncate" title="${escapeHtml(rawName)}">${escapeHtml(rawName)}</div>
        <div class="small text-secondary">
          <span class="${over ? "text-danger" : ""}">${formatMoney(actual).replace("KES", currency)}</span>
          ${
            planned === null
              ? `<span class="text-secondary"> • planned —</span>`
              : `<span class="text-secondary"> • planned ${formatMoney(planned).replace("KES", currency)}</span>`
          }
        </div>
      </div>
      <div class="progress" role="progressbar" aria-label="${escapeHtml(rawName)}" aria-valuenow="${pct}" aria-valuemin="0" aria-valuemax="100" style="height: .5rem;">
        <div class="progress-bar ${over ? "bg-danger" : ""}" style="width: ${pct}%"></div>
      </div>
    `;
    container.appendChild(card);
  }
}

async function loadActualSpending() {
  const container = byId("budgetActuals");
  if (container) container.innerHTML = `<div class="text-secondary small">Loading…</div>`;

  const api = window.mpesaApi;
  if (!api?.get) throw new Error("API helper not found. Is app.js loaded?");

  const { rows } = collectBudget();
  const summary = await api.get("/summary");
  renderActuals({ plannedRows: rows, summary });
}

function applyBudgetToForm(budget) {
  const monthEl = byId("budgetMonth");
  const incomeEl = byId("budgetIncome");
  if (monthEl && budget?.month) monthEl.value = budget.month;
  if (incomeEl) incomeEl.value = String(parseMoney(budget?.income));

  const rows = Array.isArray(budget?.rows) && budget.rows.length ? budget.rows : defaultBudgetRows();
  renderBudgetRows(rows);
  recalc();
}

function setSavedHint(text) {
  const hint = byId("budgetSavedHint");
  if (!hint) return;
  hint.textContent = text;
}

document.addEventListener("DOMContentLoaded", () => {
  const monthEl = byId("budgetMonth");
  const incomeEl = byId("budgetIncome");
  const saveBtn = byId("btnSaveBudget");
  const addBtn = byId("btnAddBudgetRow");
  const actualBtn = byId("btnLoadActuals");

  if (monthEl && !monthEl.value) monthEl.value = nowMonth();

  const initialMonth = monthEl?.value || nowMonth();
  applyBudgetToForm(loadBudget(initialMonth) || { month: initialMonth, income: 0, rows: defaultBudgetRows() });

  monthEl?.addEventListener("change", () => {
    const month = monthEl.value || nowMonth();
    setSavedHint("");
    applyBudgetToForm(loadBudget(month) || { month, income: 0, rows: defaultBudgetRows() });
  });

  incomeEl?.addEventListener("input", () => recalc());

  addBtn?.addEventListener("click", () => {
    const tbody = byId("budgetBody");
    if (!tbody) return;
    tbody.appendChild(createBudgetRow({ category: "", planned: 0 }));
    recalc();
  });

  saveBtn?.addEventListener("click", () => {
    const data = collectBudget();
    saveBudget(data.month, data);
    setSavedHint(`Saved for ${data.month}.`);
  });

  actualBtn?.addEventListener("click", async () => {
    try {
      setSavedHint("");
      await loadActualSpending();
    } catch (e) {
      const container = byId("budgetActuals");
      if (container) container.innerHTML = `<div class="text-danger small">Error: ${escapeHtml(e.message)}</div>`;
    }
  });
});

