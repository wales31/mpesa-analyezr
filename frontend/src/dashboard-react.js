const { useMemo, useState } = React;

const CURRENCY = "KES";
const formatMoney = (value) =>
  new Intl.NumberFormat("en-KE", {
    style: "currency",
    currency: CURRENCY,
    maximumFractionDigits: 0,
  }).format(value);

const MONTH_SPENDING = 86750;
const LAST_MONTH_SPENDING = 79200;
const trendPct = ((MONTH_SPENDING - LAST_MONTH_SPENDING) / LAST_MONTH_SPENDING) * 100;

const categoryData = [
  { label: "Uncategorized", value: 14200, color: "#94a3b8" },
  { label: "Shopping", value: 28600, color: "#ef4444" },
  { label: "Bills", value: 31950, color: "#f59e0b" },
  { label: "Saving", value: 12000, color: "#16a34a" },
];

const insights = [
  {
    title: "Uncategorized spend is high",
    note: "16% of your outflow is unlabeled. Categorize these to improve insights.",
    cta: "Fix categories",
  },
  {
    title: "Shopping increased this week",
    note: "Shopping is +22% vs previous week. Consider a weekly cap.",
    cta: "Set shopping cap",
  },
  {
    title: "Bills are due in 3 days",
    note: "You can pre-pay utilities now to avoid late fees.",
    cta: "Pay upcoming bills",
  },
];

const transactions = [
  { merchant: "Naivas Supermarket", amount: -3240, date: "2026-03-31T14:10:00Z" },
  { merchant: "KPLC Prepaid", amount: -2500, date: "2026-03-30T08:42:00Z" },
  { merchant: "M-Shwari Savings", amount: 4000, date: "2026-03-29T17:20:00Z" },
  { merchant: "Uber", amount: -980, date: "2026-03-29T06:55:00Z" },
  { merchant: "Safaricom Airtime", amount: -500, date: "2026-03-28T10:01:00Z" },
];

const budgetLimit = 90000;
const budgetUsed = MONTH_SPENDING;
const budgetPct = Math.min(100, (budgetUsed / budgetLimit) * 100);

function relativeDate(value) {
  const now = new Date("2026-04-01T00:00:00Z");
  const then = new Date(value);
  const diffMs = now - then;
  const day = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  if (day <= 0) return "today";
  if (day === 1) return "1 day ago";
  return `${day} days ago`;
}

function DonutChart({ data, activeIndex, onSelect }) {
  const total = data.reduce((sum, item) => sum + item.value, 0);
  let cursor = 0;

  const segments = data.map((item, index) => {
    const angle = (item.value / total) * 360;
    const start = cursor;
    cursor += angle;
    return { ...item, index, start, end: cursor, pct: ((item.value / total) * 100).toFixed(1) };
  });

  const conic = segments
    .map((segment) => `${segment.color} ${segment.start}deg ${segment.end}deg`)
    .join(", ");

  return (
    <div className="card h-full">
      <div className="card-header-row">
        <h2>Spending categories</h2>
      </div>
      <div className="donut-wrap">
        <button
          className="donut"
          style={{ background: `conic-gradient(${conic})` }}
          aria-label="Spending by category"
        >
          <span>{formatMoney(total)}</span>
        </button>
        <div className="legend">
          {segments.map((segment) => (
            <button
              key={segment.label}
              className={`legend-item ${activeIndex === segment.index ? "active" : ""}`}
              onClick={() => onSelect(segment.index)}
            >
              <span className="dot" style={{ backgroundColor: segment.color }} />
              <span>{segment.label}</span>
              <strong>{segment.pct}%</strong>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

function App() {
  const [activeCategory, setActiveCategory] = useState(0);
  const selected = useMemo(() => categoryData[activeCategory], [activeCategory]);

  return (
    <main className="dashboard">
      <section className="card hero">
        <p className="eyebrow">Monthly spending</p>
        <h1>{formatMoney(MONTH_SPENDING)}</h1>
        <p className={`trend ${trendPct <= 0 ? "positive" : "negative"}`}>
          {trendPct > 0 ? "▲" : "▼"} {Math.abs(trendPct).toFixed(1)}% vs last month
        </p>
        <div className="actions">
          <button>Send</button>
          <button>Pay Bill</button>
          <button className="primary">Analyze</button>
        </div>
      </section>

      <section className="grid-main">
        <div className="stack">
          <div className="card">
            <div className="card-header-row">
              <h2>Actionable insights</h2>
            </div>
            <div className="insights-list">
              {insights.slice(0, 3).map((item) => (
                <article className="insight" key={item.title}>
                  <div>
                    <h3>{item.title}</h3>
                    <p>{item.note}</p>
                  </div>
                  <button className="ghost">{item.cta}</button>
                </article>
              ))}
            </div>
          </div>

          <div className="card">
            <div className="card-header-row">
              <h2>Recent transactions</h2>
              <button className="text-button">View all</button>
            </div>
            <ul className="tx-list">
              {transactions.slice(0, 5).map((tx) => (
                <li className="tx-item" key={`${tx.merchant}-${tx.date}`}>
                  <div>
                    <strong>{tx.merchant}</strong>
                    <p>{relativeDate(tx.date)}</p>
                  </div>
                  <span className={tx.amount >= 0 ? "amount positive" : "amount negative"}>
                    {tx.amount >= 0 ? "+" : ""}
                    {formatMoney(tx.amount)}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="stack">
          <DonutChart data={categoryData} activeIndex={activeCategory} onSelect={setActiveCategory} />

          <div className="card">
            <h2>{selected.label} details</h2>
            <p className="muted">Tap a donut segment to inspect details (progressive disclosure).</p>
            <div className="detail-row">
              <span>Total</span>
              <strong>{formatMoney(selected.value)}</strong>
            </div>
            <div className="detail-row">
              <span>Share</span>
              <strong>{((selected.value / MONTH_SPENDING) * 100).toFixed(1)}%</strong>
            </div>
          </div>

          <div className="card">
            <h2>Budget usage</h2>
            <div className="budget-line">
              <span>{formatMoney(budgetUsed)} used</span>
              <strong>{budgetPct.toFixed(0)}%</strong>
            </div>
            <div className="progress">
              <div className={`bar ${budgetPct > 90 ? "danger" : "ok"}`} style={{ width: `${budgetPct}%` }} />
            </div>
            <p className="muted">Remaining: {formatMoney(Math.max(0, budgetLimit - budgetUsed))}</p>
            {budgetPct > 90 && <p className="warning">Warning: you are above 90% of monthly budget.</p>}
          </div>
        </div>
      </section>
    </main>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
